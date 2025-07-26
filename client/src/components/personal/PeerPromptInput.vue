<template>
  <div class="peer-prompt-input">
    <div class="input-container">
      <textarea
        ref="textareaRef"
        v-model="inputValue"
        :placeholder="placeholder"
        :maxlength="maxlength"
        class="custom-textarea"
        @input="handleInput"
        @focus="handleFocus"
        @blur="handleBlur"
        @keydown="handleKeydown"
      ></textarea>
      <div class="char-counter">
        {{ (inputValue || '').length }} / {{ maxlength }}
      </div>
    </div>
    
    <!-- 下拉建议框 -->
    <div 
      v-if="showSuggestions && suggestions.length > 0"
      class="suggestions-dropdown"
      :style="{ top: dropdownTop + 'px' }"
    >
      <div
        v-for="(suggestion, index) in suggestions"
        :key="index"
        class="suggestion-item"
        :class="{ 'active': index === activeIndex }"
        @click="selectSuggestion(suggestion)"
        @mouseenter="activeIndex = index"
      >
        {{ suggestion }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue';

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  suggestions: {
    type: Array,
    default: () => []
  },
  placeholder: {
    type: String,
    default: '请输入内容...'
  },
  maxlength: {
    type: Number,
    default: 100
  }
});

const emit = defineEmits(['update:modelValue', 'select']);

const textareaRef = ref(null);
const inputValue = ref(props.modelValue);
const showSuggestions = ref(false);
const activeIndex = ref(-1);
const dropdownTop = ref(0);

// 监听 modelValue 变化
watch(() => props.modelValue, (newVal) => {
  inputValue.value = newVal;
});

// 监听输入值变化
watch(inputValue, (newVal) => {
  emit('update:modelValue', newVal);
});

function handleInput() {
  // 输入时显示建议
  showSuggestions.value = true;
  activeIndex.value = -1;
  updateDropdownPosition();
}

function handleFocus() {
  // 获得焦点时显示所有建议
  showSuggestions.value = true;
  updateDropdownPosition();
}

function handleBlur() {
  // 延迟隐藏，避免点击建议项时立即隐藏
  setTimeout(() => {
    showSuggestions.value = false;
    activeIndex.value = -1;
  }, 200);
}

function handleKeydown(e) {
  if (!showSuggestions.value || props.suggestions.length === 0) return;
  
  switch (e.key) {
    case 'ArrowDown':
      e.preventDefault();
      activeIndex.value = Math.min(activeIndex.value + 1, props.suggestions.length - 1);
      break;
    case 'ArrowUp':
      e.preventDefault();
      activeIndex.value = Math.max(activeIndex.value - 1, -1);
      break;
    case 'Enter':
      e.preventDefault();
      if (activeIndex.value >= 0) {
        selectSuggestion(props.suggestions[activeIndex.value]);
      }
      break;
    case 'Escape':
      showSuggestions.value = false;
      activeIndex.value = -1;
      break;
  }
}

function selectSuggestion(suggestion) {
  inputValue.value = suggestion;
  showSuggestions.value = false;
  activeIndex.value = -1;
  emit('select', suggestion);
  
  // 聚焦到输入框
  nextTick(() => {
    textareaRef.value?.focus();
  });
}

function updateDropdownPosition() {
  if (textareaRef.value) {
    const rect = textareaRef.value.getBoundingClientRect();
    dropdownTop.value = rect.height + 5; // 输入框下方5px
  }
}
</script>

<style scoped>
.peer-prompt-input {
  position: relative;
  width: 100%;
}

.input-container {
  position: relative;
}

.custom-textarea {
  width: 100%;
  min-height: 120px;
  padding: 8px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  font-size: 13px;
  line-height: 1.5;
  resize: vertical;
  font-family: inherit;
  background-color: #fff;
  transition: border-color 0.2s;
  box-sizing: border-box;
}

.custom-textarea:focus {
  outline: none;
  border-color: #409eff;
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.2);
}

.custom-textarea::placeholder {
  color: #c0c4cc;
}

.char-counter {
  position: absolute;
  bottom: 13px;
  right: 12px;
  font-size: 12px;
  color: #909399;
  background-color: rgba(255, 255, 255, 0.9);
  padding: 2px 6px;
  border-radius: 2px;
}

.suggestions-dropdown {
  position: absolute;
  left: 0;
  right: 0;
  background: #fff;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  z-index: 1000;
  max-height: 200px;
  overflow-y: auto;
}

.suggestion-item {
  padding: 8px;
  cursor: pointer;
  border-bottom: 1px solid #f5f7fa;
  font-size: 13px;
  line-height: 1.4;
  transition: background-color 0.2s;
}

.suggestion-item:last-child {
  border-bottom: none;
}

.suggestion-item:hover,
.suggestion-item.active {
  background-color: #f5f7fa;
  color: #409eff;
}

.suggestion-item:first-child {
  border-radius: 4px 4px 0 0;
}

.suggestion-item:last-child {
  border-radius: 0 0 4px 4px;
}
</style> 