// 等级转换工具测试文件
import { translateLevelType, getDistributionTypeLabel } from './levelTranslations.js';

// 测试等级类型转换
console.log('=== 等级类型转换测试 ===');
console.log('Normal Speech ->', translateLevelType('Normal Speech'));
console.log('High Edit ->', translateLevelType('High Edit'));
console.log('Low Browsing ->', translateLevelType('Low Browsing'));
console.log('Normal Participation ->', translateLevelType('Normal Participation'));

// 测试组内分布标签
console.log('\n=== 组内分布标签测试 ===');
console.log('normal ->', getDistributionTypeLabel('normal'));
console.log('high ->', getDistributionTypeLabel('high'));
console.log('low ->', getDistributionTypeLabel('low'));
console.log('dominant ->', getDistributionTypeLabel('dominant'));

// 测试包含等级关键词的文本
console.log('\n=== 包含等级关键词的文本测试 ===');
console.log('用户发言等级为 Normal Speech ->', translateLevelType('用户发言等级为 Normal Speech'));
console.log('编辑行为 High Edit 需要关注 ->', translateLevelType('编辑行为 High Edit 需要关注')); 