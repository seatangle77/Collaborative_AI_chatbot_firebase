<template>
  <div class="note-editor">
    <div v-if="showTitle" class="note-title-wrapper">
      <div class="note-title">协作笔记</div>
      <el-button
        style="display: none"
        size="small"
        class="start-write-btn"
        type="primary"
        @click="$emit('start-edit')"
        >开始写入数据</el-button
      >
    </div>

    <div ref="editorContainer" class="quill-editor"></div>
    <div class="editor-footer">
      <div class="word-count">字数: {{ wordCount }}</div>
      <div class="save-status" :class="{ saving: isSaving, saved: isSaved }">
        {{ saveStatusText }}
      </div>
    </div>
  </div>
</template>

<script setup>
import * as Y from "yjs";
import { QuillBinding } from "y-quill";
import Quill from "quill";
import { WebsocketProvider } from "y-websocket";
import hljs from "highlight.js";
import "highlight.js/styles/github.css";

import {
  ref,
  onMounted,
  onBeforeUnmount,
  reactive,
  watch,
  nextTick,
} from "vue";
import {
  doc,
  getDoc,
  setDoc,
  serverTimestamp,
  collection,
  addDoc,
  Timestamp,
} from "firebase/firestore";
import { collection as firestoreCollection } from "firebase/firestore"; // 避免命名冲突
import { firestore } from "@/firebase"; // 请确保你的 firebase 配置文件路径正确
import { debounce } from "lodash-es";
// 移除 getGroupSocketStatus 相关导入
// import { getGroupSocketStatus } from "@/services/groupWebSocketManager";
import { watch as vueWatch } from "vue";

import Delta from "quill-delta";
import apiService from "@/services/apiService";

const props = defineProps({
  noteId: {
    type: String,
    required: true,
  },
  userId: {
    type: String,
    required: true,
  },
  members: {
    type: Array,
    required: false,
    default: () => [],
  },
  editorStarted: {
    type: Boolean,
    default: false,
  },
  readOnly: {
    type: Boolean,
    default: false,
  },
  showTitle: {
    type: Boolean,
    default: true,
  },
  currentUserId: {
    type: String,
    required: true,
  },
});

import { computed } from "vue";

function getRandomColor() {
  const colors = [
    "#1a365d", // 深蓝色
    "#2d3748", // 深灰色
    "#742a2a", // 深红色
    "#22543d", // 深绿色
    "#553c9a", // 深紫色
    "#744210", // 深棕色
    "#2c7a7b", // 深青色
    "#4a5568", // 深灰蓝色
    "#2d3748", // 深灰
    "#1a202c", // 深黑
  ];
  return colors[Math.floor(Math.random() * colors.length)];
}

function generateEditSummary(delta) {
  const actions = [];
  if (delta.ops.some(op => op.insert && typeof op.insert === 'string')) actions.push("插入文字");
  if (delta.ops.some(op => op.insert && typeof op.insert !== 'string')) actions.push("插入对象（如图片/视频）");
  if (delta.ops.some(op => op.delete)) actions.push("删除内容");
  if (delta.ops.some(op => op.attributes?.bold)) actions.push("加粗");
  if (delta.ops.some(op => op.attributes?.italic)) actions.push("斜体");
  if (delta.ops.some(op => op.attributes?.underline)) actions.push("下划线");
  if (delta.ops.some(op => op.attributes?.strike)) actions.push("删除线");
  if (delta.ops.some(op => op.attributes?.color)) actions.push("更改文字颜色");
  if (delta.ops.some(op => op.attributes?.background)) actions.push("更改背景色");
  if (delta.ops.some(op => op.attributes?.link)) actions.push("插入/编辑链接");
  if (delta.ops.some(op => op.attributes?.image)) actions.push("插入图片");
  if (delta.ops.some(op => op.attributes?.video)) actions.push("插入视频");
  if (delta.ops.some(op => op.attributes?.code)) actions.push("插入代码");
  if (delta.ops.some(op => op.attributes?.blockquote)) actions.push("插入引用");
  if (delta.ops.some(op => op.attributes?.header)) actions.push("设置为标题");
  if (delta.ops.some(op => op.attributes?.list)) actions.push("设置为列表");
  if (delta.ops.some(op => op.attributes?.align)) actions.push("更改对齐方式");
  if (delta.ops.some(op => op.attributes?.indent)) actions.push("更改缩进");
  if (delta.ops.some(op => op.attributes?.font)) actions.push("更改字体");
  if (delta.ops.some(op => op.attributes?.size)) actions.push("更改字号");
  // ...可继续扩展
  if (actions.length > 0) {
    return actions.join("、");
  }
  return "未知操作";
}

function getAffectedTextFromDelta(delta, quillInstance) {
  try {
    const results = [];
    let index = 0;

    for (const op of delta.ops) {
      if (op.retain && op.attributes) {
        let segment = quillInstance.getText(index, op.retain || 0);
        if (segment.trim() === "" && op.retain === 1) {
          // 获取行范围文本作为段落样式影响内容
          const [line, offset] = quillInstance.getLine(index);
          segment = line?.domNode?.innerText || "(空段)";
        }
        results.push({
          text: segment.trim(),
          formats: op.attributes,
          startIndex: index,
          length: op.retain,
        });
      }

      if (op.retain) {
        index += op.retain;
      } else if (op.insert) {
        index += typeof op.insert === "string" ? op.insert.length : 1;
      } else if (op.delete) {
        // do nothing
      }
    }

    if (results.length > 0) {
      return results
        .map((seg) => {
          const displayText = seg.text || "(空)";
          const styleDesc = Object.entries(seg.formats)
            .map(([k, v]) => `${k}: ${v}`)
            .join(", ");
          return `将"${displayText}"设为样式（${styleDesc}）`;
        })
        .join("；");
    }

    // fallback to original behavior for insert/delete
    let idx = 0;
    let length = 0;
    for (const op of delta.ops) {
      if (op.retain) idx += op.retain;
      if (op.insert) {
        length = typeof op.insert === "string" ? op.insert.length : 1;
        break;
      }
      if (op.delete) {
        length = op.delete;
        break;
      }
    }
    return quillInstance.getText(idx, length).trim();
  } catch (err) {
    console.warn("⚠️ Failed to extract affected text:", err);
    return "";
  }
}

const currentMember = computed(() =>
  props.members.find((m) => m.user_id === props.userId)
);

const editorContainer = ref(null);
const wordCount = ref(0);
const isSaving = ref(false);
const isSaved = ref(false);
const saveStatusText = ref("已保存");

const ydoc = new Y.Doc();
const provider = new WebsocketProvider(
  "wss://yjs-server-lime.onrender.com",
  `note-${props.noteId}`,
  ydoc
);
const ytext = ydoc.getText("quill");

watch(
  () => props.userId,
  (newUserId) => {
    const newMember = props.members.find((m) => m.user_id === newUserId);
    provider.awareness.setLocalStateField("user", {
      name: newMember?.name || "未知用户",
      color: newMember?.color || getRandomColor(),
    });
  },
  { immediate: true }
);

// 移除 triggerSaveUserId 相关 watch 逻辑

const contentRef = doc(firestore, "note_contents", props.noteId);
const historyRef = firestoreCollection(firestore, "note_edit_history");
let hasInsertedInitialContent = false;

let quill;
let deltaFlushInterval;
let isApplyingColor = false;

onMounted(async () => {
  await nextTick(); // 确保 DOM 完全挂载
  console.log("[NoteEditor挂载] noteId:", props.noteId, "userId:", props.userId, "members:", props.members);

  if (editorContainer.value) {
    // 定义工具栏配置
    const toolbarOptions = [
      [{ header: [1, 2, 3, 4, 5, 6, false] }],
      ["bold", "italic", "underline", "strike"],
      [{ color: [] }, { background: [] }],
      [{ font: [] }],
      [{ size: ["small", false, "large", "huge"] }],
      [{ list: "ordered" }, { list: "bullet" }, { list: "check" }],
      [{ script: "sub" }, { script: "super" }],
      [{ indent: "-1" }, { indent: "+1" }],
      [{ direction: "rtl" }],
      [{ align: [] }],
      ["blockquote", "code-block"],
      ["link", "image", "video"],
      ["undo", "redo"],
      ["clean"],
    ];

    quill = new Quill(editorContainer.value, {
      theme: "snow",
      modules: {
        toolbar: toolbarOptions,
        history: {
          delay: 2000,
          maxStack: 500,
          userOnly: true,
        },
      },
      placeholder: "开始编写你的协作笔记...",
      readOnly: props.readOnly, // 根据 props 控制只读
    });
    // 监听 selection-change 事件，更新本地 awareness 的 cursor 字段
    quill.on("selection-change", (range, oldRange, source) => {
      if (source !== "user") return;
      provider.awareness.setLocalStateField("cursor", range);
    });
  } else {
    console.warn("❗ editorContainer is null, cannot initialize Quill");
    return;
  }

  // 初始化时同步一次字数
  wordCount.value = quill.getText().trim().length;

  console.log("✅ Quill initialized", quill);

  // 添加自定义工具栏按钮
  const toolbar = quill.getModule("toolbar");

  // 添加撤销/重做按钮
  toolbar.addHandler("undo", function () {
    quill.history.undo();
  });

  toolbar.addHandler("redo", function () {
    quill.history.redo();
  });

  // 添加工具栏提示
  const toolbarButtons =
    toolbar.container.querySelectorAll("button, .ql-picker");
  toolbarButtons.forEach((button) => {
    button.addEventListener("mouseenter", function () {
      const title = this.getAttribute("data-value") || this.title;
      if (title) {
        this.setAttribute("title", title);
      }
    });
  });

  if (editorContainer.value && editorContainer.value.firstChild) {
    new QuillBinding(ytext, quill, provider.awareness);
  } else {
    console.warn(
      "❗ editorContainer has no valid child, skipping QuillBinding init"
    );
  }

  const pendingDeltas = [];
  let lastContentSavedAt = Date.now();

  quill.on("text-change", (delta, oldDelta, source) => {
    if (!true || source !== "user") return;
    if (isApplyingColor) return;
    // 只读模式下不处理编辑事件
    if (props.readOnly) return;

    pendingDeltas.push(delta);

    // 更新字数统计
    const text = quill.getText();
    wordCount.value = text.trim().length;
    // 更新保存状态
    isSaving.value = true;
    isSaved.value = false;
    saveStatusText.value = "保存中...";
  });

  function combineDeltas(deltas) {
    return deltas.reduce((acc, d) => acc.compose(new Delta(d)), new Delta());
  }

  let lastSavedDelta = quill.getContents(); // 初始 delta

  // 每 5 秒合并一次 delta，记录编辑行为
  deltaFlushInterval = setInterval(() => {
    if (!props.editorStarted) return;
    // 只读模式下不记录编辑历史
    if (props.readOnly) return;
    try {
      console.log('[NoteEditor] 当前userId:', props.userId, 'currentUserId:', props.currentUserId);
      // 只记录当前登录用户的编辑历史
      if (props.userId !== props.currentUserId) return;
      const currentDelta = quill.getContents();
      const deltaChanged =
        JSON.stringify(currentDelta.ops) !== JSON.stringify(lastSavedDelta.ops);

      if (pendingDeltas.length === 0 && !deltaChanged) return;

      // 遍历pendingDeltas，为每个delta生成摘要
      if (pendingDeltas.length > 0) {
        const summaries = pendingDeltas.map(d => ({
          summary: generateEditSummary(d),
          delta: d
        }));
        console.log('10秒内所有操作摘要：', summaries);
      }

      const combinedDelta =
        pendingDeltas.length > 0
          ? combineDeltas(pendingDeltas)
          : currentDelta.diff(lastSavedDelta);

      pendingDeltas.length = 0;
      lastSavedDelta = currentDelta;

      const summary = generateEditSummary(combinedDelta);
      const affectedText = getAffectedTextFromDelta(combinedDelta, quill);

      console.log("将要写入 note_edit_history：", {
        userId: props.userId,
        delta: combinedDelta.ops.map((op) => ({ ...op })),
        charCount: combinedDelta.length(),
        isDelete: combinedDelta.ops?.some((op) => op.delete),
        hasHeader: combinedDelta.ops?.some((op) => op.attributes?.header),
        hasList: combinedDelta.ops?.some((op) => op.attributes?.list),
        updatedAt: new Date().toISOString(),
        summary,
        affectedText,
      });
      apiService.saveNoteEditHistory({
        noteId: props.noteId,
        userId: props.userId,
        delta: combinedDelta.ops.map((op) => ({ ...op })),
        charCount: combinedDelta.length(),
        isDelete: combinedDelta.ops?.some((op) => op.delete),
        hasHeader: combinedDelta.ops?.some((op) => op.attributes?.header),
        hasList: combinedDelta.ops?.some((op) => op.attributes?.list),
        updatedAt: new Date().toISOString(),
        summary,
        affectedText: affectedText,
      })
        .then(() => {
          isSaving.value = false;
          isSaved.value = true;
          saveStatusText.value = "已保存";
          setTimeout(() => {
            isSaved.value = false;
          }, 3000);
        })
        .catch((error) => {
          isSaving.value = false;
          saveStatusText.value = "保存失败";
          console.error("❌ Failed to save edit log", error);
        });
    } catch (err) {
      console.error("❌ Interval execution failed:", err);
    }
  }, 10000);

  provider.awareness.on("change", () => {
    // 不再需要更新 collaborators，因为 collaborators 变量已删除
  });

  // 不再依赖 noteRef 读取旧数据，统一使用 note_contents 表存储内容

  ytext.observe(() => {
    // 只要内容有变化就统计字数（包括只读模式下的协作同步）
    if (!props.editorStarted) return;
    if (!quill) return;
    wordCount.value = quill.getText().trim().length;
    // 只读模式下不保存内容
    if (props.readOnly) return;
    // 只记录当前登录用户的内容
    if (props.userId !== props.currentUserId) return;
    const now = Date.now();
    if (now - lastContentSavedAt >= 60000) {
      // 采用 quill.root.innerHTML 作为富文本存储
      const delta = quill.getContents();
      const html = quill.root.innerHTML;
      if (!delta || delta.length() === 0) {
        console.log("⚠️ Skipped saving because delta is empty");
        return;
      }
      // 📤 Attempting to save content to note_contents
      console.log("将要写入 note_contents：", {
        noteId: props.noteId,
        userId: props.userId,
        content: delta.ops.map((op) => ({ ...op })), // 保留 Delta 格式以备分析
        html, // 可粘贴富文本格式
        updatedAt: new Date().toISOString(),
      });
      apiService.saveNoteContent({
        noteId: props.noteId,
        userId: props.userId,
        content: delta.ops.map((op) => ({ ...op })), // 保留 Delta 格式以备分析
        html, // 可粘贴富文本格式
        updatedAt: new Date().toISOString(),
      })
        .then(() => {
          lastContentSavedAt = now;
        })
        .catch((err) => {
          console.error("❌ Failed to save note content", err);
        });
    }
  });

  // 移除监听 group WebSocket 状态的逻辑
  // vueWatch(getGroupSocketStatus, (newStatus) => {
  //   if (newStatus === "connected" && !props.editorStarted) {
  //     console.log("🟢 WebSocket 连接成功，自动触发写入数据");
  //   }
  // });
});

onBeforeUnmount(() => {
  provider.awareness.off("change", () => {
    // 不再需要更新 collaborators，因为 collaborators 变量已删除
  });
  clearInterval(deltaFlushInterval);
  try {
    provider.disconnect();
    provider.destroy();
    ydoc.destroy();
  } catch (e) {
    console.warn("⚠️ Cleanup error:", e);
  }
});

</script>

<style scoped>
@import "quill/dist/quill.snow.css";

.start-write-btn {
  height: 32px;
}

.note-editor {
  background-color: #fdfdfd;
  border-radius: 8px;
  font-size: 15px;
  line-height: 1.7;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border: 1px solid #e1e5e9;
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
}

.note-title-wrapper {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.note-title {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 16px;
}

.quill-editor {
  flex: 1 1 0%;
  min-height: 0;
  border: 1px solid #e1e5e9;
  background-color: #fff;
  border-radius: 8px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.quill-editor .ql-toolbar {
  border-bottom: 1px solid #e1e5e9;
  background-color: #f8f9fa;
  flex-shrink: 0;
  overflow-x: auto;
  white-space: nowrap;
}
.ql-toolbar.ql-snow{
  padding: 3px;
}

.quill-editor .ql-container {
  font-size: 14px;
  line-height: 1.6;
  flex: 1;
  overflow: hidden;
}

.quill-editor .ql-editor {
  min-height: 350px;
  padding: 20px;
  overflow-wrap: break-word;
  word-wrap: break-word;
  word-break: break-word;
}

.quill-editor .ql-editor p {
  margin-bottom: 12px;
}

.quill-editor .ql-editor h1,
.quill-editor .ql-editor h2,
.quill-editor .ql-editor h3,
.quill-editor .ql-editor h4,
.quill-editor .ql-editor h5,
.quill-editor .ql-editor h6 {
  margin-top: 20px;
  margin-bottom: 12px;
  font-weight: 600;
}

.quill-editor .ql-editor blockquote {
  border-left: 4px solid #007bff;
  padding-left: 16px;
  margin: 16px 0;
  color: #6c757d;
}

.quill-editor .ql-editor code {
  background-color: #f8f9fa;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: "Monaco", "Menlo", "Ubuntu Mono", monospace;
}

.quill-editor .ql-editor pre {
  background-color: #f8f9fa;
  padding: 16px;
  border-radius: 6px;
  overflow-x: auto;
  margin: 16px 0;
}

.editor-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 3px 16px;
  background-color: #f8f9fa;
  border-top: 1px solid #e1e5e9;
  font-size: 12px;
  color: #6c757d;
  flex-shrink: 0;
}

.word-count {
  font-weight: 500;
}

.save-status {
  display: flex;
  align-items: center;
  gap: 4px;
}

.save-status.saving {
  color: #ffc107;
}

.save-status.saved {
  color: #28a745;
}

.save-status.saving::before {
  content: "";
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: #ffc107;
  animation: pulse 1.5s infinite;
}

.save-status.saved::before {
  content: "✓";
  color: #28a745;
  font-weight: bold;
}

@keyframes pulse {
  0% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
  100% {
    opacity: 1;
  }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .note-editor {
    padding: 12px;
  }

  .quill-editor {
    height: 300px;
  }

  .quill-editor .ql-editor {
    padding: 12px;
    min-height: 250px;
  }

  .editor-footer {
    flex-direction: column;
    gap: 4px;
    align-items: flex-start;
  }

  .quill-editor .ql-toolbar {
    flex-wrap: wrap;
  }

  .quill-editor .ql-toolbar .ql-formats {
    margin-bottom: 4px;
  }
}

/* 用户编辑颜色样式 */
.quill-editor .ql-editor .ql-cursor {
  border-left: 2px solid;
  border-right: none;
  margin-left: -1px;
  margin-right: -1px;
  pointer-events: none;
}

.quill-editor .ql-editor .ql-cursor::before {
  content: "";
  position: absolute;
  top: -2px;
  left: -2px;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: inherit;
  border: 1px solid #fff;
  box-shadow: 0 0 2px rgba(0, 0, 0, 0.3);
}

/* 用户选择文本的高亮颜色 */
.quill-editor .ql-editor .ql-selection {
  background: rgba(0, 0, 0, 0.1);
}

/* 确保用户颜色在编辑器中可见 */
.quill-editor .ql-editor [data-yjs-user] {
  background-color: rgba(0, 0, 0, 0.05);
  border-radius: 2px;
  padding: 1px 2px;
}

/* 用户编辑颜色样式 - 深色系 */
.quill-editor .ql-editor [data-yjs-user] {
  position: relative;
  border-radius: 2px;
  padding: 2px 4px;
  margin: 1px 0;
}

/* 深色系用户颜色 - 使用 CSS 变量 */
.quill-editor .ql-editor [data-yjs-user-color="#1a365d"] {
  background-color: rgba(26, 54, 93, 0.08);
  border-left: 3px solid #1a365d;
  padding-left: 8px;
  margin-left: -8px;
}

.quill-editor .ql-editor [data-yjs-user-color="#2d3748"] {
  background-color: rgba(45, 55, 72, 0.08);
  border-left: 3px solid #2d3748;
  padding-left: 8px;
  margin-left: -8px;
}

.quill-editor .ql-editor [data-yjs-user-color="#742a2a"] {
  background-color: rgba(116, 42, 42, 0.08);
  border-left: 3px solid #742a2a;
  padding-left: 8px;
  margin-left: -8px;
}

.quill-editor .ql-editor [data-yjs-user-color="#22543d"] {
  background-color: rgba(34, 84, 61, 0.08);
  border-left: 3px solid #22543d;
  padding-left: 8px;
  margin-left: -8px;
}

.quill-editor .ql-editor [data-yjs-user-color="#553c9a"] {
  background-color: rgba(85, 60, 154, 0.08);
  border-left: 3px solid #553c9a;
  padding-left: 8px;
  margin-left: -8px;
}

.quill-editor .ql-editor [data-yjs-user-color="#744210"] {
  background-color: rgba(116, 66, 16, 0.08);
  border-left: 3px solid #744210;
  padding-left: 8px;
  margin-left: -8px;
}

.quill-editor .ql-editor [data-yjs-user-color="#2c7a7b"] {
  background-color: rgba(44, 122, 123, 0.08);
  border-left: 3px solid #2c7a7b;
  padding-left: 8px;
  margin-left: -8px;
}

.quill-editor .ql-editor [data-yjs-user-color="#4a5568"] {
  background-color: rgba(74, 85, 104, 0.08);
  border-left: 3px solid #4a5568;
  padding-left: 8px;
  margin-left: -8px;
}

.quill-editor .ql-editor [data-yjs-user-color="#1a202c"] {
  background-color: rgba(26, 32, 44, 0.08);
  border-left: 3px solid #1a202c;
  padding-left: 8px;
  margin-left: -8px;
}
/* Slightly increase height of summary note editor */
:deep(.summary-editor .quill-editor .ql-editor) {
  min-height: 360px;
  margin-bottom: 0;
}
:deep(.ql-toolbar.ql-snow) {
  padding: 3px !important;
}
:deep(.ql-picker-options) {
  max-height: 220px;
  overflow-y: auto;
  z-index: 9999;
}
</style>
