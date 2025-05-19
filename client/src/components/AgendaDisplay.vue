<template>
  <el-card class="agenda-display">
    <!-- 🔹 Group Info Section -->
    <div :class="['group-info', { 'group-info-edit': groupInfoEditMode }]">
      <div class="group-header">
        <div class="group-name">👥 {{ groupName }}</div>
        <span
          class="edit-icon"
          @click="toggleGroupInfoEdit"
          style="cursor: pointer; margin-left: 8px"
        >
          <svg
            v-if="!groupInfoEditMode"
            t="1743569691776"
            class="icon"
            viewBox="0 0 1024 1024"
            version="1.1"
            xmlns="http://www.w3.org/2000/svg"
            p-id="2112"
            width="20"
            height="20"
          >
            <path
              d="M486.6 156c-1.1-1.2-1.7-2.2-2.7-3.4L123.3 525.9 104.2 545C78.4 570.6 64 605.4 64 641.8v103.5c0 19.8 15.3 35.5 34.2 35.5H200c33.2 0 65.1-13.2 88.7-36.6l22.8-22.5 356.2-369.2c-25-26.5-57-61.4-89.7-96.3-38.1-41.7-69.1-75.5-91.4-100.2zM538.2 97.4zM726.4 131.2l-32.7-33.8C673.3 76 645.3 64 616 64c-29.4 0.1-57.5 12.1-77.8 33.4 60.9 66.9 122.4 133.3 184.4 199.3l3.8-4.5c43-44.4 43-116.5 0-161zM927 714.7H436.8c-18.3 0-33 14.8-33 33 0 18.3 14.8 33 33 33H927c18.3 0 33-14.8 33-33s-14.8-33-33-33zM927 596.2H565.6c-18.3 0-33 14.8-33 33 0 18.3 14.8 33 33 33H927c18.3 0 33-14.8 33-33s-14.8-33-33-33zM927 477.6H696.2c-18.3 0-33 14.8-33 33 0 18.3 14.8 33 33 33H927c18.3 0 33-14.8 33-33s-14.8-33-33-33z"
              p-id="2113"
              fill="#909399"
            ></path>
          </svg>
          <svg
            v-else
            t="1743570220298"
            class="icon"
            viewBox="0 0 1024 1024"
            version="1.1"
            xmlns="http://www.w3.org/2000/svg"
            p-id="3244"
            width="20"
            height="20"
          >
            <path
              d="M475 276V141.4c-12.1-56.3-58.2-22-58.2-22L96.6 395.9c-70.4 48.9-4.8 85.7-4.8 85.7l315.4 274.1c63.1 46.5 67.9-24.5 67.9-24.5V606.4C795.3 506 926.3 907.5 926.3 907.5c12.1 22 19.4 0 19.4 0C1069.4 305.4 475 276 475 276z"
              p-id="3245"
              fill="#909399"
            ></path>
          </svg>
        </span>
      </div>
      <template v-if="!groupInfoEditMode">
        <div class="group-item">
          <span class="group-topic">Group Goal</span>
          <p class="group-description">{{ groupGoal }}</p>
        </div>
      </template>
      <template v-else>
        <el-form
          label-position="top"
          class="edit-form"
          style="margin-top: 10px"
        >
          <el-form-item label="Group Name" style="font-weight: 600">
            <el-input v-model="editableGroupName" size="small" />
          </el-form-item>
          <el-form-item label="Group Goal" style="font-weight: 600">
            <el-input
              v-model="editableGroupGoal"
              type="textarea"
              :rows="2"
              size="small"
            />
          </el-form-item>
        </el-form>
        <div style="margin-top: 8px; text-align: right">
          <el-button type="success" @click="submitGroupInfo">
            ✅ Submit
          </el-button>
        </div>
      </template>
    </div>
    <!-- 📌 Current Agenda -->
    <div class="agenda-header">
      <span class="agenda-title">
        📌 Current Agenda
        <span
          class="edit-icon"
          @click="agendaEditMode = !agendaEditMode"
          style="cursor: pointer; margin-left: 8px"
        >
          <svg
            v-if="!agendaEditMode"
            t="1743569691776"
            class="icon"
            viewBox="0 0 1024 1024"
            version="1.1"
            xmlns="http://www.w3.org/2000/svg"
            p-id="2112"
            width="20"
            height="20"
          >
            <path
              d="M486.6 156c-1.1-1.2-1.7-2.2-2.7-3.4L123.3 525.9 104.2 545C78.4 570.6 64 605.4 64 641.8v103.5c0 19.8 15.3 35.5 34.2 35.5H200c33.2 0 65.1-13.2 88.7-36.6l22.8-22.5 356.2-369.2c-25-26.5-57-61.4-89.7-96.3-38.1-41.7-69.1-75.5-91.4-100.2zM538.2 97.4zM726.4 131.2l-32.7-33.8C673.3 76 645.3 64 616 64c-29.4 0.1-57.5 12.1-77.8 33.4 60.9 66.9 122.4 133.3 184.4 199.3l3.8-4.5c43-44.4 43-116.5 0-161zM927 714.7H436.8c-18.3 0-33 14.8-33 33 0 18.3 14.8 33 33 33H927c18.3 0 33-14.8 33-33s-14.8-33-33-33zM927 596.2H565.6c-18.3 0-33 14.8-33 33 0 18.3 14.8 33 33 33H927c18.3 0 33-14.8 33-33s-14.8-33-33-33zM927 477.6H696.2c-18.3 0-33 14.8-33 33 0 18.3 14.8 33 33 33H927c18.3 0 33-14.8 33-33s-14.8-33-33-33z"
              p-id="2113"
              fill="#909399"
            ></path>
          </svg>
          <svg
            v-else
            t="1743570220298"
            class="icon"
            viewBox="0 0 1024 1024"
            version="1.1"
            xmlns="http://www.w3.org/2000/svg"
            p-id="3244"
            width="20"
            height="20"
          >
            <path
              d="M475 276V141.4c-12.1-56.3-58.2-22-58.2-22L96.6 395.9c-70.4 48.9-4.8 85.7-4.8 85.7l315.4 274.1c63.1 46.5 67.9-24.5 67.9-24.5V606.4C795.3 506 926.3 907.5 926.3 907.5c12.1 22 19.4 0 19.4 0C1069.4 305.4 475 276 475 276z"
              p-id="3245"
              fill="#909399"
            ></path>
          </svg>
        </span>
      </span>
      <el-tag type="info" class="agenda-count"
        >{{ agendas.length }} items</el-tag
      >
    </div>

    <!-- 📌 Agenda List -->
    <div class="agenda-list">
      <div
        v-for="(agenda, index) in agendas"
        :key="agenda.id"
        class="agenda-item"
        :class="agendaEditMode ? '' : getStatusClass(agenda.status)"
      >
        <div class="agenda-main">
          <div class="agenda-content">
            <template v-if="agendaEditMode">
              <el-form :model="agenda" label-position="top" class="edit-form">
                <el-form-item label="Title" style="font-weight: 600">
                  <el-input v-model="agenda.agenda_title" size="small" />
                </el-form-item>
                <el-form-item label="Description" style="font-weight: 600">
                  <el-input
                    v-model="agenda.agenda_description"
                    type="textarea"
                    :rows="3"
                    size="small"
                  />
                </el-form-item>
              </el-form>
              <div class="agenda-delete-wrapper">
                <el-button
                  type="danger"
                  size="small"
                  class="delete-icon-btn"
                  @click="deleteAgenda(agenda, index)"
                  title="Delete Agenda"
                >
                  <svg
                    t="1743574257296"
                    class="icon"
                    viewBox="0 0 1024 1024"
                    version="1.1"
                    xmlns="http://www.w3.org/2000/svg"
                    p-id="4368"
                    width="18"
                    height="18"
                  >
                    <path
                      d="M256 810.666667c0 46.933333 38.4 85.333333 85.333333 85.333333l341.333333 0c46.933333 0 85.333333-38.4 85.333333-85.333333L768 298.666667 256 298.666667 256 810.666667zM810.666667 170.666667l-149.333333 0-42.666667-42.666667-213.333333 0-42.666667 42.666667L213.333333 170.666667l0 85.333333 597.333333 0L810.666667 170.666667z"
                      p-id="4369"
                      fill="#909399"
                    ></path>
                  </svg>
                </el-button>
              </div>
            </template>
            <template v-else>
              <span class="agenda-topic">{{ agenda.agenda_title }}</span>
            </template>
          </div>

          <!-- 🔹 Status Emoji -->
          <template v-if="!agendaEditMode">
            <div class="status-indicator" @click="toggleAgendaStatus(agenda)">
              {{ getStatusEmoji(agenda.status) }}
            </div>
          </template>
        </div>

        <!-- 🔹 Agenda Details -->
        <template v-if="agendaEditMode">
          <!-- Agenda details are included in the edit form -->
        </template>
        <template v-else>
          <p class="agenda-description">{{ agenda.agenda_description }}</p>
        </template>
      </div>
      <div v-if="agendaEditMode" class="add-agenda">
        <el-button
          type="primary"
          @click="addNewAgenda"
          :disabled="agendas.length >= 6"
        >
          ➕ Add Agenda
        </el-button>
        <el-button
          type="success"
          @click="submitAgendas"
          style="margin-left: 12px"
        >
          ✅ Submit
        </el-button>
      </div>
    </div>
  </el-card>
</template>

<script setup>
// 新增方法：切换组信息编辑模式
const toggleGroupInfoEdit = () => {
  if (!groupInfoEditMode.value) {
    editableGroupName.value = props.groupName;
    editableGroupGoal.value = props.groupGoal;
  }
  groupInfoEditMode.value = !groupInfoEditMode.value;
};
import { ref, watch, onMounted, defineEmits } from "vue";
import { ElMessage } from "element-plus";
import api from "../services/apiService";
import "element-plus/es/components/icon/style/css";

const props = defineProps({
  agendas: Array,
  groupName: String,
  groupGoal: String,
  groupId: String,
  sessionId: String,
});

// New edit mode state
const emit = defineEmits(["refreshAgendas", "updateGroupInfo"]);
const agendaEditMode = ref(false);
const groupInfoEditMode = ref(false);

// New editable group name and goal
const editableGroupName = ref(props.groupName);
const editableGroupGoal = ref(props.groupGoal);
watch(
  () => [props.groupName, props.groupGoal],
  ([newName, newGoal]) => {
    editableGroupName.value = newName;
    editableGroupGoal.value = newGoal;
  }
);

// ✅ **Toggle Agenda Status**
const toggleAgendaStatus = async (agenda) => {
  const statusCycle = {
    not_started: "in_progress",
    in_progress: "completed",
    completed: "not_started",
  };

  const newStatus = statusCycle[agenda.status] || "not_started";
  try {
    const res = await api.toggleAgendaStatus(agenda.id, newStatus);

    if (res.message === "Agenda updated") {
      agenda.status = newStatus;
      ElMessage.success(`Status updated to: ${getStatusLabel(newStatus)}`);
    } else {
      throw new Error("Update failed");
    }
  } catch (error) {
    console.error("Failed to update agenda", error);
    ElMessage.error("Update failed, please try again later");
  }
};

const submitGroupInfo = async () => {
  try {
    await api.updateGroupInfo(props.groupId, {
      name: editableGroupName.value,
      group_goal: editableGroupGoal.value,
    });
    ElMessage.success("Group info updated successfully!");
    emit("refreshAgendas");
    groupInfoEditMode.value = false;
    emit("updateGroupInfo", {
      name: editableGroupName.value,
      goal: editableGroupGoal.value,
    });
  } catch (error) {
    console.error("Failed to update group info", error);
    ElMessage.error("Failed to update group info");
  }
};

// ✅ **Status Mapping**
const getStatusLabel = (status) => {
  const statusMap = {
    not_started: "Not Started",
    in_progress: "In Progress",
    completed: "Completed",
  };
  return statusMap[status] || "Unknown";
};

// ✅ **Status Emoji**
const getStatusEmoji = (status) => {
  const emojiMap = {
    not_started: "⏳",
    in_progress: "🚀",
    completed: "✅",
  };
  return emojiMap[status] || "❓";
};

// ✅ **Status Styles**
const getStatusClass = (status) => {
  return {
    "agenda-not-started": status === "not_started",
    "agenda-in-progress": status === "in_progress",
    "agenda-completed": status === "completed",
  };
};

const addNewAgenda = () => {
  if (props.agendas.length >= 6) return;
  props.agendas.push({
    id: Date.now().toString(), // Temporary ID
    agenda_title: "",
    agenda_description: "",
    status: "not_started",
    group_id: props.groupId,
    session_id: props.sessionId,
  });
};

// ✅ **Submit Agendas**
const submitAgendas = async () => {
  try {
    const updatePromises = props.agendas.map((agenda) => {
      // Check if it's a new agenda (not UUID or marked as isNew)
      const isNew = !/^[0-9a-fA-F-]{36}$/.test(agenda.id);
      if (isNew) {
        console.log("🟢 Submit parameters", {
          group_id: props.groupId,
          session_id: props.sessionId,
          agenda_title: agenda.agenda_title,
          agenda_description: agenda.agenda_description,
          status: "not_started",
        });
        return api.createAgenda({
          group_id: props.groupId,
          session_id: props.sessionId,
          agenda_title: agenda.agenda_title,
          agenda_description: agenda.agenda_description,
          status: "not_started",
        });
      } else {
        return api.updateAgenda(agenda.id, {
          agenda_title: agenda.agenda_title,
          agenda_description: agenda.agenda_description,
          status: "not_started",
        });
      }
    });
    await Promise.all(updatePromises);

    // Update group information
    try {
      await api.updateGroupInfo(props.groupId, {
        name: editableGroupName.value,
        group_goal: editableGroupGoal.value,
      });
    } catch (error) {
      console.error("Failed to update group info", error);
    }

    ElMessage.success("Agenda submitted successfully!");
    emit("refreshAgendas"); // Notify parent component to refresh agenda data
    agendaEditMode.value = false;
  } catch (error) {
    console.error("Submit failed", error);
    ElMessage.error("Submit failed, please try again later");
  }
};

// ✅ **Delete Agenda**
const deleteAgenda = async (agenda, index) => {
  const isNew = !/^[0-9a-fA-F-]{36}$/.test(agenda.id);
  if (isNew) {
    // Frontend newly added unsubmitted agenda, directly remove from array
    props.agendas.splice(index, 1);
  } else {
    try {
      const res = await api.deleteAgenda(agenda.id);
      if (res.message === "Agenda deleted") {
        props.agendas.splice(index, 1);
        ElMessage.success("Agenda deleted");
        emit("refreshAgendas");
      } else {
        throw new Error("Delete failed");
      }
    } catch (error) {
      console.error("Delete failed", error);
      ElMessage.error("Delete failed, please try again later");
    }
  }
};
</script>

<style scoped>
/* 🔹 Agenda Overall */
.agenda-display {
  width: 100%;
  height: 100%;
  padding: 20px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 3px 8px rgba(0, 0, 0, 0.08);
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}
.add-agenda {
  display: flex;
  justify-content: center;
  margin-top: 12px;
}
.group-info {
  margin-bottom: 30px;
  padding: 12px;
  font-size: 14px;
  color: #444;
  line-height: 1.6;
  border-radius: 10px;
  transition: all 0.3s ease;
  background: linear-gradient(135deg, #fff7e1, #ffebcc);
  border-left: 5px solid #ff9800;
}

.group-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.group-name {
  font-size: 20px;
  font-weight: 700;
  color: #ff9800;
}
.group-item {
  border-radius: 12px;
  padding: 15px;
  transition: background 0.3s ease;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.group-topic {
  font-size: 16px;
  font-weight: 700;
  color: #333;
}
.group-description {
  font-size: 14px;
  color: #555;
  line-height: 1.5;
}

/* 🔹 Title Bar */
.agenda-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 18px;
  font-weight: bold;
  margin-bottom: 20px;
}

.agenda-title {
  font-size: 20px;
  font-weight: 700;
  color: #2878ff;
}

/* 🔹 Agenda List */
.agenda-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
  flex: 1;
}

/* 🔹 Agenda Item - Different Status Colors */
.agenda-item {
  border-radius: 12px;
  padding: 15px;
  transition: background 0.3s ease;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

/* 🟡 Not Started */
.agenda-not-started {
  background: linear-gradient(135deg, #fff7e1, #ffebcc);
  border-left: 5px solid #ff9800;
}

/* 🔵 In Progress */
.agenda-in-progress {
  background: linear-gradient(135deg, #e1f2ff, #cce7ff);
  border-left: 5px solid #007bff;
}

/* 🟢 Completed */
.agenda-completed {
  background: linear-gradient(135deg, #e1ffe1, #ccffcc);
  border-left: 5px solid #00a000;
}

/* 🔹 Agenda Main Line */
.agenda-main {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

/* 🔹 Agenda Title */
.agenda-content {
  display: flex;
  flex-direction: row;
  justify-content: space-between;
  align-items: center;
  flex: 0.95;
}

.agenda-topic {
  font-size: 16px;
  font-weight: 700;
  color: #333;
}

/* 🔹 Agenda Details */
.agenda-description {
  font-size: 14px;
  color: #555;
  line-height: 1.5;
}

/* 🔹 Status Indicator */
.status-indicator {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  font-size: 20px;
  display: flex;
  justify-content: center;
  align-items: center;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 3px 5px rgba(0, 0, 0, 0.1);
  background: white;
}

.status-indicator:hover {
  transform: scale(1.1);
  opacity: 0.8;
}

.agenda-delete-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background-color: #fef0f0;
  cursor: pointer;
  transition: background-color 0.3s ease;
}

.agenda-delete-wrapper:hover {
  background-color: #fde2e2;
}

.delete-icon-btn {
  margin: 0;
  padding: 0;
  border: none;
  background: none;
}
.edit-form {
  background: #ffffff;
  padding: 12px;
  border-radius: 10px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
  flex: 0.95;
}
.edit-form .el-form-item {
  margin-bottom: 10px;
}
.group-info-edit {
  background: transparent !important;
  border-left: none !important;
}
</style>
