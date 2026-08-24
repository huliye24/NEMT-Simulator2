# NEMT Simulator 云端上传计划 - 200步

## 上传策略

**规则：**
- 每步上传一个或多个相关文件
- 按功能模块分组
- 优先上传核心代码，文档可选

---

## 第一阶段：基础设施 (1-30步)

### 1. 根目录配置
```
Step 1:  README.md, CLAUDE.md
Step 2:  requirements.txt, pyproject.toml
Step 3:  .env.example, .coveragerc
Step 4:  .flake8, .pre-commit-config.yaml, pytest.ini
Step 5:  Dockerfile, docker-compose.yml, docker-compose.prod.yml
```

### 2. 核心NEMT模块
```
Step 6:   nemt_core.py, main.py
Step 7:   nemt_execution.py, nemt_controller.py
Step 8:   nemt_brain.py (brain_layer.py)
Step 9:   nemt_state_machine.py
Step 10:  nemt_risk.py, nemt_signals.py
Step 11:  nemt_probability_execution.py
Step 12:  nemt_spatial_temporal.py
Step 13:  nemt_volatility_model.py
Step 14:  nemt_economic_analysis.py
Step 15:  nemt_theory_config.json
```

### 3. AI安全模块
```
Step 16:  ai_safety.py, ai_safety.bat
Step 17:  ai_safety_emergency.bat, ai_safety_rollback.bat
Step 18:  ai_safety_snap.bat
Step 19:  ai_sip_quick.bat, ai_sip_startup.bat
Step 20:  architecture_guard.py, architecture_guard.bat
Step 21:  direction_lock.py, direction_lock.bat
Step 22:  cognitive_router.py, cognitive_router.bat
Step 23:  state_recovery.py, state_recovery.bat
Step 24:  refactor_limit.py, refactor_limit.bat
```

### 4. 云端连接模块
```
Step 25:  cloud_status.py, check_status.py
Step 26:  cloud_server_connect.py, cloud_ssh_connect.py
Step 27:  check_cloud_server.py, check_services.py
Step 28:  cloud_view_code.py
Step 29:  start_wede.py, start_wede_v2.py
Step 30:  install_wede.py, fix_wede.py, fix_wede_config.py
```

---

## 第二阶段：数据与API (31-50步)

### 5. 数据获取
```
Step 31:  data_fetcher.py, binance_fetcher.py
Step 32:  fetch_notion.py, fetch_page2.py
Step 33:  fetch_page_cloud.py, fetch_page_save.py
Step 34:  fetch_notion_v2.py, fetch_notion_v3.py
Step 35:  cloud_fetch_pages.py
Step 36:  data/ 目录
```

### 6. Notion同步
```
Step 37:  notion_setup.py, notion_theory_sync.py
Step 38:  create_notion_obsidian.py
Step 39:  upload_nemt_notion.py, upload_vision.py
Step 40:  upload_all_notion.py, upload_notion_tar.py
Step 41:  simple_notion_structure.py
```

### 7. API与测试
```
Step 42:  test_api.go
Step 43:  confirm_status.py
Step 44:  debug_page.py, fetch_founder_agent.py
Step 45:  get_page_via_cloud.py, quick_fetch_notion.py
```

---

## 第三阶段：回测系统 (46-70步)

### 8. 回测引擎
```
Step 46:  backtest_engine.py
Step 47:  enhanced_phase_detector.py
Step 48:  entropy_simulation.py, entropy_sim_v2.py
Step 49:  experiments.py, benchmark.py
Step 50:  entropy_simulation_result.txt
```

### 9. backtest目录
```
Step 51:  backtest/__init__.py
Step 52:  backtest/models/__init__.py, market.py
Step 53:  backtest/tests/__init__.py
Step 54:  backtest/tests/test_loaders.py
Step 55:  backtest/tests/test_models.py
Step 56:  backtest/tests/test_processors.py
```

### 10. 回测数据
```
Step 57:  matlab_data/ 目录
Step 58:  output/ 目录
Step 59:  results/ 目录
Step 60:  data/ 目录
```

---

## 第四阶段：NEMT-OS核心 (71-110步)

### 11. nemt_os 核心
```
Step 71:  nemt_os/nemt/__init__.py, config/
Step 72:  nemt_os/nemt/core/ 核心文件
Step 73:  nemt_os/nemt/brain.py
Step 74:  nemt_os/nemt/risk.py
Step 75:  nemt_os/nemt/market_providers/
```

### 12. nemt_os 适配器
```
Step 76:  nemt_os/nemt/adapters/ 目录
Step 77:  nemt_os/nemt_backup_20260427/ 备份文件
```

### 13. NEMT-Quant-OS
```
Step 78:  NEMT_Quant_OS_Design.md
Step 79:  NEMT_Quant_OS_Electron.md
Step 80:  NEMT_Electron_Architecture.md
```

---

## 第五阶段：前端与UI (111-140步)

### 14. Electron桌面应用
```
Step 111: electron/package.json, package-lock.json
Step 112: electron/src/main.ts
Step 113: electron/src/main/*.ts
Step 114: electron/src/preload.ts
Step 115: electron/src/types/
Step 116: electron/tsconfig.json, build.js
```

### 15. Web前端
```
Step 120: web/COMPONENTS.md
Step 121: web/index.html
Step 122: web/*.html, web/assets/
Step 123: web/js/, web/css/
```

### 16. nemt-web
```
Step 125: nemt-web/ 目录
```

---

## 第六阶段：容器与部署 (141-160步)

### 17. Docker配置
```
Step 141: docker/Dockerfile, docker/Dockerfile.api
Step 142: docker/Dockerfile.frontend, Dockerfile.market
Step 143: docker/Dockerfile.risk, Dockerfile.signal
Step 144: docker/docker-compose.yml
Step 145: docker/build.sh, docker/gateway/, docker/frontend/
```

### 18. Kubernetes配置
```
Step 150: k8s/nemt/ 目录
Step 151: k8s/argocd/ 目录
```

---

## 第七阶段：Go微服务 (161-180步)

### 19. nemt-go
```
Step 161: nemt-go/go.mod, nemt-go/go.sum
Step 162: nemt-go/Dockerfile, Makefile
Step 163: nemt-go/pkg/common/, nemt-go/pkg/config/
Step 164: nemt-go/pkg/bootstrap/
Step 165: nemt-go/pkg/cache/
Step 166: nemt-go/pkg/collector/
Step 167: nemt-go/pkg/decision/
Step 168: nemt-go/pkg/evolution/
Step 169: nemt-go/pkg/gateway/
Step 170: nemt-go/cmd/collector/, cmd/gateway/
Step 171: nemt-go/cmd/scheduler/
```

---

## 第八阶段：工具与文档 (181-200步)

### 20. 工具脚本
```
Step 181: scripts/ 目录
Step 182: tasks/ 目录
Step 183: setup_cloud_server.py, setup_lightweight_remote.py
Step 184: ssh_*.py 系列
Step 185: install_*.py 系列
Step 186: test_*.py 系列
```

### 21. 文档
```
Step 190: SPEC.md, PRD.md, TASKS.md
Step 191: CHANGELOG.md, LICENSE
Step 192: FLOWS.md, CODE_REVIEW_CHECKLIST.md
Step 193: SECURITY_AUDIT_REPORT.md, SECURITY_FIX_REPORT.md
Step 194: docs/ 部分文档
Step 195: docs/ 剩余文档
```

### 22. 杂项
```
Step 198: 配置文件 (config/)
Step 199: 图片资源 (recruitment-*.png, *.html)
Step 200: 最后清理与验证
```

---

## 执行方式

### 方式A: 批量执行
```bash
python upload_step.py --range 1-50
```

### 方式B: 单步执行
```bash
python upload_step.py --step 1
```

### 方式C: 按阶段执行
```bash
python upload_phase.py --phase 1  # 基础设施
```

---

## 进度追踪

上传进度保存在: `cloud_dev/upload_progress.json`

```json
{
  "current_step": 50,
  "total_steps": 200,
  "completed": [1, 2, 3, ...],
  "failed": [],
  "last_update": "2026-05-03 12:30"
}
```
