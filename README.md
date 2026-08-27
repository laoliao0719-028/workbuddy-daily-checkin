# WorkBuddy 每日自动签到（GitHub Actions 版）

不依赖任何电脑，纯云端每天定时签到。电脑报废 / 只有手机也能跑。

## 原理
- `daily_checkin.py`：调用 `https://copilot.tencent.com/v2/billing/meter/daily-checkin`，用 Bearer token 签到。
- `.github/workflows/daily-checkin.yml`：GitHub Actions 每天 **北京时间 09:00**（UTC 01:00）自动运行脚本。
- token 通过仓库 **Secret** 注入，不写进代码，避免泄露。

## 部署步骤（一次性）
1. 在 GitHub 新建一个**私有**仓库（如 `workbuddy-daily-checkin`）。
2. 把本仓库的 `daily_checkin.py` 和 `.github/workflows/daily-checkin.yml` 上传进去。
3. 仓库 `Settings → Secrets and variables → Actions → New repository secret`：
   - Name: `WORKBUDDY_ACCOUNTS`
   - Secret: 见下方「Secret 值」（由部署人提供，是一行 JSON）
4. `Actions` 标签页开启该 workflow；可点 `Run workflow` 手动跑一次验证。

## Secret 值（WORKBUDDY_ACCOUNTS）
由部署人生成并提供，格式：
```json
{"accounts":[{"name":"鸵鸟","token":"<从 workbuddy-desktop.info 读取的 accessToken>"}]}
```

## token 过期与更新
- `accessToken` 是 JWT，约 **58 天**后过期（首次部署约到 2026-10-25）。
- 过期后脚本会报「失效」，GitHub Actions 运行记录变红。此时在手机上打开 GitHub 网页：
  仓库 `Settings → Secrets → WORKBUDDY_ACCOUNTS → Update`，
  把新 token 粘贴进去即可（新 token 取自本机 `workbuddy-desktop.info` 的 `auth.accessToken`）。
- 若长期想免维护，可把桌面客户端保持登录，并改用 refresh 流程（见脚本外说明）。

## 可选：微信/手机通知
脚本支持 PushPlus / Server 酱，在 Secrets 再加：
- `PUSHPLUS_TOKEN`（PushPlus 令牌）→ 推送到微信
- `SERVERCHAN_KEY`（Server 酱 Key）→ 推送到微信
不加也能正常签到，只是没有推送消息。
