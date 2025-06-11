// 获取本地存储的 token
function getToken() {
  return new Promise((resolve) => {
    chrome.storage.local.get(["authToken"], (result) => {
      resolve(result.authToken || "");
    });
  });
}

// 设置 token（你可以从 popup 或登录流程中设置）
function setToken(token) {
  return chrome.storage.local.set({ authToken: token });
}