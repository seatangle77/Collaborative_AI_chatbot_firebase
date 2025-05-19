<template>
  <el-card class="user-profile-card" v-if="user">
    <div class="user-info">
      <el-avatar :src="user.avatar_link" size="large" />
      <div class="edit-toggle">
        <svg
          v-if="!editMode"
          @click="editMode = true"
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
          @click="editMode = false"
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
      </div>
      <template v-if="editMode">
        <el-input v-model="editedUser.name" placeholder="Enter name" />
        <div class="section user-background">
          <strong>Background</strong>
          <div style="margin-top: 8px">
            <label><strong>Major:</strong></label>
            <el-input
              v-model="editedUser.academic_background.major"
              placeholder="Enter major"
              class="input-field"
            />
          </div>
          <div style="margin-top: 12px">
            <label><strong>Research Focus:</strong></label>
            <el-input
              v-model="editedUser.academic_background.research_focus"
              placeholder="Enter research focus"
              class="input-field"
            />
          </div>
        </div>
        <div class="section user-advantages">
          <strong>Strengths:</strong>
          <el-input v-model="editedUser.academic_advantages" type="textarea" />
        </div>
        <el-button
          type="success"
          @click="saveUserInfo"
          style="margin-left: 12px"
        >
          ✅ Submit
        </el-button>
      </template>
      <template v-else>
        <div class="user-name">{{ user.name }}</div>
        <div class="section user-background">
          <strong>Background</strong>
          <div v-if="user.academic_background">
            <div>
              <strong>Major:</strong> {{ user.academic_background.major }}
            </div>
            <div>
              <strong>Research Focus:</strong>
              {{ user.academic_background.research_focus }}
            </div>
          </div>
        </div>
        <div class="section user-advantages">
          <strong>Strengths:</strong> {{ user.academic_advantages }}
        </div>
      </template>
    </div>
  </el-card>
</template>

<script setup>
import { ref, watch } from "vue";
import api from "../services/apiService";
import { ElMessage } from "element-plus";

const props = defineProps({
  user: {
    type: Object,
    default: null,
  },
});

const editMode = ref(false);
const editedUser = ref({});

watch(
  () => props.user,
  (newUser) => {
    editedUser.value = JSON.parse(JSON.stringify(newUser || {}));
  },
  { immediate: true }
);

const saveUserInfo = async () => {
  try {
    await api.updateUser(editedUser.value.user_id, {
      name: editedUser.value.name,
      academic_background: editedUser.value.academic_background,
      academic_advantages: editedUser.value.academic_advantages,
    });
    Object.assign(props.user, editedUser.value);
    editMode.value = false;
    ElMessage.success("User info updated successfully!");
  } catch (error) {
    console.error("用户信息更新失败:", error);
  }
};
</script>

<style scoped>
.user-profile-card {
  width: 100%;
  max-width: none;
  padding: 16px;
  border-radius: 8px;
  background-color: #ffffff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  text-align: left;
}

.user-info {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 12px;
  position: relative;
}

.user-details {
  margin-left: 0;
  margin-top: 12px;
  text-align: center;
}

.user-name {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 4px;
  color: #1f2d3d;
}

.user-background,
.user-advantages {
  font-size: 14px;
  margin-top: 6px;
}

.section {
  font-size: 14px;
  color: #3c3c3c;
  line-height: 1.6;
  margin-top: 8px;
}

.section strong {
  color: #2878ff;
  font-weight: 500;
}

.edit-toggle {
  position: absolute;
  top: 8px;
  right: 12px;
  cursor: pointer;
}
.input-field {
  width: 100%;
  margin-top: 4px;
}
</style>
