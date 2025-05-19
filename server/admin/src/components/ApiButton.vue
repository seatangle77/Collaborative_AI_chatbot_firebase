<template>
  <div>
    <el-button type="primary" @click="fetchData">{{ label }}</el-button>

    <el-tag
      v-if="status"
      :type="status === 'success' ? 'success' : 'danger'"
      class="status-tag"
    >
      {{ status }}
    </el-tag>

    <el-table v-if="responseData.length > 0" :data="responseData" border>
      <el-table-column
        v-for="(value, key) in responseData[0]"
        :key="key"
        :prop="key"
        :label="key"
      />
    </el-table>

    <p v-if="responseData.length === 0">没有数据</p>
  </div>
</template>

<script setup>
import { ref, defineProps, defineEmits } from "vue";
import axios from "axios";
import { ElMessage } from "element-plus";

const props = defineProps({
  apiUrl: String,
  label: String,
});

const responseData = ref([]);
const status = ref("");

const emit = defineEmits(["api-status", "api-data"]);

const fetchData = async () => {
  try {
    const response = await axios.get(props.apiUrl);
    responseData.value = response.data;
    status.value = "success";
    emit("api-status", "success");
    emit("api-data", response.data);
    ElMessage.success(`${props.label} - 数据加载成功`);
  } catch (error) {
    responseData.value = [];
    status.value = "error";
    emit("api-status", "error");
    emit("api-data", []);
    ElMessage.error(`${props.label} - 数据加载失败`);
  }
};
</script>

<style scoped>
.el-button {
  margin-right: 10px;
}

.status-tag {
  margin-left: 10px;
}
</style>
