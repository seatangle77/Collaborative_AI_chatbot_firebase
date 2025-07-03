<template>
  <div class="note-editor">
    <div class="note-title-wrapper">
      <div class="note-title">协作笔记</div>
      <el-button size="small" class="start-write-btn" type="primary" @click="editorStarted = true"
        >开始写入数据</el-button
      >
    </div>
    <div class="collaborators">
      <span
        v-for="(user, index) in collaborators"
        :key="index"
        class="collaborator"
      >
        <span
          class="collaborator-avatar"
          :style="{ backgroundColor: user.color }"
          :title="user.name"
        >
          {{ user.name[0] }}
        </span>
      </span>
    </div>
    <div ref="editorContainer" class="quill-editor"></div>
  </div>
</template>

<script setup>
import * as Y from "yjs";
import { QuillBinding } from "y-quill";
import Quill from "quill";
import { WebsocketProvider } from "y-websocket";
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
import { connectionStatus } from '@/services/websocketManager';
import { watch as vueWatch } from 'vue';

import Delta from "quill-delta";

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
});

import { computed } from "vue";

function getRandomColor() {
  const colors = [
    "#f94144",
    "#f3722c",
    "#f8961e",
    "#f9844a",
    "#f9c74f",
    "#90be6d",
    "#43aa8b",
    "#577590",
  ];
  return colors[Math.floor(Math.random() * colors.length)];
}

function generateEditSummary(delta) {
  if (delta.ops.some((op) => op.insert)) return "插入文字";
  if (delta.ops.some((op) => op.delete)) return "删除文字";
  if (delta.ops.some((op) => op.attributes?.header)) return "设置为标题样式";
  if (delta.ops.some((op) => op.attributes?.list)) return "设置为列表格式";
  return "样式修改";
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
        console.log("📌 正在处理 retain + attributes 类型：", {
          index,
          retain: op.retain,
          segment,
        });
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
const editorStarted = ref(false);
const ydoc = new Y.Doc();
const provider = new WebsocketProvider(
  "wss://yjs-server-lime.onrender.com",
  `note-${props.noteId}`,
  ydoc
);
const ytext = ydoc.getText("quill");
const collaborators = reactive([]);

function updateCollaborators() {
  collaborators.length = 0;
  const states = Array.from(provider.awareness.getStates().values());
  for (const state of states) {
    if (state.user) collaborators.push(state.user);
  }
}

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

const contentRef = doc(firestore, "note_contents", props.noteId);
const historyRef = firestoreCollection(firestore, "note_edit_history");
let hasInsertedInitialContent = false;

let quill;
let deltaFlushInterval;

onMounted(async () => {
  await nextTick(); // 确保 DOM 完全挂载
  console.log("📦 Quill container loaded:", editorContainer.value);

  if (editorContainer.value) {
    quill = new Quill(editorContainer.value, {
      theme: "snow",
    });
  } else {
    console.warn("❗ editorContainer is null, cannot initialize Quill");
    return;
  }

  console.log("✅ Quill initialized", quill);

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
    if (!editorStarted.value || source !== "user") return;
    pendingDeltas.push(delta);
  });

  function combineDeltas(deltas) {
    return deltas.reduce((acc, d) => acc.compose(new Delta(d)), new Delta());
  }

  let lastSavedDelta = quill.getContents(); // 初始 delta

  // 每 5 秒合并一次 delta，记录编辑行为
  deltaFlushInterval = setInterval(() => {
    try {
      if (!editorStarted.value) return;
      const currentDelta = quill.getContents();
      const deltaChanged =
        JSON.stringify(currentDelta.ops) !== JSON.stringify(lastSavedDelta.ops);

      if (pendingDeltas.length === 0 && !deltaChanged) return;

      const combinedDelta =
        pendingDeltas.length > 0
          ? combineDeltas(pendingDeltas)
          : currentDelta.diff(lastSavedDelta);

      pendingDeltas.length = 0;
      lastSavedDelta = currentDelta;

      const summary = generateEditSummary(combinedDelta);
      const affectedText = getAffectedTextFromDelta(combinedDelta, quill);

      addDoc(historyRef, {
        userId: props.userId,
        delta: combinedDelta.ops.map((op) => ({ ...op })),
        charCount: combinedDelta.length(),
        isDelete: combinedDelta.ops?.some((op) => op.delete),
        hasHeader: combinedDelta.ops?.some((op) => op.attributes?.header),
        hasList: combinedDelta.ops?.some((op) => op.attributes?.list),
        updatedAt: new Date().toISOString(),
        summary,
        affectedText,
      })
        .then(() => {
          console.log("📝 [Auto] Edit log saved (fallback or normal)");
        })
        .catch((error) => {
          console.error("❌ Failed to save edit log", error);
          console.log("❗ combinedDelta:", combinedDelta);
        });
    } catch (err) {
      console.error("❌ Interval execution failed:", err);
    }
  }, 10000);

  provider.awareness.on("change", updateCollaborators);
  updateCollaborators();

  // 不再依赖 noteRef 读取旧数据，统一使用 note_contents 表存储内容

  ytext.observe(() => {
    if (!editorStarted.value) return;
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
      console.log("📤 Attempting to save content to note_contents:", {
        content: delta.ops.map((op) => ({ ...op })),
        html,
        userId: props.userId,
        noteId: props.noteId,
      });
      addDoc(firestoreCollection(firestore, "note_contents"), {
        noteId: props.noteId,
        userId: props.userId,
        content: delta.ops.map((op) => ({ ...op })), // 保留 Delta 格式以备分析
        html, // 可粘贴富文本格式
        updatedAt: new Date().toISOString(),
      })
        .then(() => {
          console.log("💾 Note content saved to note_contents");
        })
        .catch((err) => {
          console.error("❌ Failed to save note content", err);
        });
      lastContentSavedAt = now;
    }
  });

  // 监听 WebSocket 连接成功，自动触发"开始写入数据"
  vueWatch(connectionStatus, (newStatus) => {
    if (newStatus === 'connected' && !editorStarted.value) {
      editorStarted.value = true;
      console.log('🟢 WebSocket 连接成功，自动触发写入数据');
    }
  });
});

onBeforeUnmount(() => {
  provider.awareness.off("change", updateCollaborators);
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
  padding: 20px;
  background-color: #fdfdfd;
  border-radius: 6px;
  font-size: 15px;
  line-height: 1.7;
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
  height: 400px;
  border: 1px solid #aaa;
  background-color: #fff;
}

.collaborators {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.collaborator-avatar {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: bold;
  color: white;
}
</style>
