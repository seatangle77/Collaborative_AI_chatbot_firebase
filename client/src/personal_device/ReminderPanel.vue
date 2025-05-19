<template>
  <el-card class="reminder-panel">
    <h3>回顾</h3>
    <p>{{ reviewText }}</p>
    <el-button @click="fetchReview">回顾15秒</el-button>
  </el-card>
</template>
<script setup>
import { ref } from "vue";
import apiService from "../services/apiService";
const reviewText = ref("");
const fetchReview = async () => {
  reviewText.value = await apiService.getReview();
};
</script>
