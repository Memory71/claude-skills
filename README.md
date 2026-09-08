# claude-skills

自用的 [Claude Skills](https://docs.claude.com/en/docs/agents-and-tools/agent-skills/overview) 集合，一個子目錄一個 skill。

## Skills

| Skill | 用途 |
|---|---|
| [`exam-drill-builder`](./exam-drill-builder) | 把公開題庫 PDF 轉成練習教材：無答案練習 PDF、解答對照表、單檔 HTML 刷題器 |

## 安裝方式

Claude 的 skill 是以資料夾為單位上傳的，所以要把單一 skill 打包成 zip：

```bash
git clone https://github.com/Memory71/claude-skills.git
cd claude-skills
zip -r exam-drill-builder.zip exam-drill-builder -x "*__pycache__*"
```

接著到 Claude 的 **設定 → Capabilities → Skills** 上傳該 zip。上傳後在**新開的對話**才會生效。

zip 內的最上層必須是 skill 資料夾本身（`exam-drill-builder/SKILL.md`），
不能是資料夾裡的檔案（`SKILL.md` 直接躺在 zip 根目錄）。

## 撰寫慣例

- 資料夾名稱必須與 `SKILL.md` frontmatter 的 `name` 欄位一致，否則安裝後路徑對不上
- `description` 要寫出**觸發時機**（使用者會怎麼開口），不只寫功能，否則 Claude 不會在對的時候叫用它
- 可執行的腳本放 `scripts/`，模板與靜態檔放 `assets/`
- 踩過的坑要寫進 SKILL.md。那份文件是給未來的 Claude 看的，不是給人看的說明書

## 授權

MIT。各 skill 處理的題庫、資料來源等內容不包含在本 repo 內，其權利歸原權利人所有。
