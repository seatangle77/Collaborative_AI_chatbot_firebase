// 等级类型中文转换工具

const levelMappings = {
    // 发言等级
    'Normal Speech': '正常发言',
    'High Speech': '高频率发言',
    'Low Speech': '低频率发言',
    'No Speech': '无发言',
    'Dominant Speech': '主导发言',

    // 编辑等级
    'Normal Edit': '正常编辑',
    'High Edit': '高频率编辑',
    'Low Edit': '低频率编辑',
    'No Edit': '无编辑',
    'Dominant Edit': '主导编辑',

    // 浏览等级
    'Normal Browsing': '正常浏览',
    'High Browsing': '高频率浏览',
    'Low Browsing': '低频率浏览',
    'No Browsing': '无浏览',
    'Dominant Browsing': '主导浏览',

    // 参与类型
    'Normal Participation': '正常参与',
    'High Participation': '高参与度',
    'Low Participation': '低参与度',
    'No Participation': '无参与',
    'Dominant Participation': '主导参与',

    // 其他可能的等级
    'Normal': '正常',
    'High': '高',
    'Low': '低',
    'No': '无',
    'Dominant': '主导'
};

/**
 * 将英文等级类型转换为中文
 * @param {string} text - 要转换的文本
 * @returns {string} - 转换后的中文文本
 */
export function translateLevelType(text) {
    if (!text) return text;

    // 如果完全匹配，直接返回
    if (levelMappings[text]) {
        return levelMappings[text];
    }

    // 如果包含等级关键词，进行部分替换
    let translatedText = text;
    Object.entries(levelMappings).forEach(([en, zh]) => {
        translatedText = translatedText.replace(new RegExp(en, 'g'), zh);
    });

    return translatedText;
}

/**
 * 获取组内分布类型的中文标签
 * @param {string} type - 分布类型
 * @returns {string} - 中文标签
 */
export function getDistributionTypeLabel(type) {
    const labels = {
        'normal': '正常参与',
        'high': '高参与度',
        'low': '低参与度',
        'dominant': '主导型',
        'no': '无参与'
    };
    return labels[type] || type;
}

export default {
    translateLevelType,
    getDistributionTypeLabel
}; 