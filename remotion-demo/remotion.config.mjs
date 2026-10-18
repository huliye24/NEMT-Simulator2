import {Config} from '@remotion/cli/config';

// 本项目用 JSX（未安装 typescript / @types/react），显式指定入口
Config.setEntryPoint('src/index.js');

Config.setVideoImageFormat('jpeg');
Config.setOverwriteOutput(true);

// 本机 WorkBuddy 的 safe-delete 钩子会拦截 Node fs.unlink，
// 导致 Remotion 自动下载 Chrome Headless Shell 失败。
// 改用系统已安装的 Google Chrome 渲染，效果一致且可离线复现。
Config.setBrowserExecutable('C:/Program Files/Google/Chrome/Application/chrome.exe');
