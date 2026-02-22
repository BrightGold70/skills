# 中文文案排版指北 · 参考

本文档为 [SKILL.md](SKILL.md) 的补充：完整规则说明、自动化工具列表与参考文献。来源：[sparanoid/chinese-copywriting-guidelines](https://github.com/sparanoid/chinese-copywriting-guidelines)。

---

## 空格（细则）

- **中英文之间**：增加空格。例：在 LeanCloud 上，数据存储是围绕 `AVObject` 进行的。
- **中文与数字之间**：增加空格。例：今天出去买菜花了 5000 元。
- **数字与单位之间**：增加空格。例：10 Gbps、20 TB。**例外**：度数（90°）、百分比（15%）与数字之间不加空格。
- **全角标点**与相邻字符之间不加空格。
- CSS：`text-spacing`（CSS Text Module Level 4）与 `-ms-text-autospace` 可自动加空格，但尚未普及，建议继续手加空格。

---

## 标点（细则）

- 不重复使用标点（！！、？？ 等）。
- 中文使用全角标点；数字使用半角；完整英文句、英文书名等使用半角标点，书名用斜体不用中文书名号。

---

## 名词（细则）

- 专有名词按官方或通用大小写书写（如 GitHub、Foursquare、Microsoft Corporation）。视觉上需全大/小写时，用 CSS `text-transform` 控制。
- 避免不地道缩写：写全称或通用缩写（如 TypeScript 而非 Ts，HTML5 而非 h5）。

---

## 自动化工具

| 仓库 | 系列 | 语言 |
|------|------|------|
| [pangu.js](https://github.com/vinta/pangu.js) | pangu | JavaScript |
| [pangu-go](https://github.com/vinta/pangu) | pangu | Go |
| [pangu.java](https://github.com/vinta/pangu.java) | pangu | Java |
| [pangu.py](https://github.com/vinta/pangu.py) | pangu | Python |
| [pangu.rb](https://github.com/dlackty/pangu.rb) | pangu | Ruby |
| [pangu.php](https://github.com/cchlorine/pangu.php) | pangu | PHP |
| [pangu.vim](https://github.com/hotoo/pangu.vim) | pangu | Vim |
| [vue-pangu](https://github.com/serkodev/vue-pangu) | pangu | Vue.js (Web Converter) |
| [intellij-pangu](https://plugins.jetbrains.com/plugin/19665-pangu) | pangu | Intellij Platform Plugin |
| [autocorrect](https://github.com/huacnlee/autocorrect) | autocorrect | Rust, WASM, CLI tool |
| [autocorrect-node](https://github.com/huacnlee/autocorrect/tree/main/autocorrect-node) | autocorrect | Node.js |
| [autocorrect-py](https://github.com/huacnlee/autocorrect/tree/main/autocorrect-py) | autocorrect | Python |
| [autocorrect-rb](https://github.com/huacnlee/autocorrect/tree/main/autocorrect-rb) | autocorrect | Ruby |
| [autocorrect-java](https://github.com/huacnlee/autocorrect/tree/main/autocorrect-java) | autocorrect | Java |
| [autocorrect-go](https://github.com/longbridgeapp/autocorrect) | autocorrect | Go |
| [autocorrect-php](https://github.com/NauxLiu/auto-correct) | autocorrect | PHP |
| [autocorrect-vscode](https://marketplace.visualstudio.com/items?itemName=huacnlee.autocorrect) | autocorrect | VS Code Extension |
| [autocorrect-idea-plugin](https://plugins.jetbrains.com/plugin/20244-autocorrect) | autocorrect | Intellij Platform Plugin |
| [jxlwqq/chinese-typesetting](https://github.com/jxlwqq/chinese-typesetting) | other | PHP |
| [sparanoid/space-lover](https://github.com/sparanoid/space-lover) | other | PHP (WordPress) |
| [sparanoid/grunt-auto-spacing](https://github.com/sparanoid/grunt-auto-spacing) | other | Node.js (Grunt) |
| [hjiang/scripts/add-space-between-latin-and-cjk](https://github.com/hjiang/scripts/blob/master/add-space-between-latin-and-cjk) | other | Python |
| [hustcc/hint](https://github.com/hustcc/hint) | other | Python |
| [n0vad3v/Tekorrect](https://github.com/n0vad3v/Tekorrect) | other | Python |

---

## 参考文献

- [Guidelines for Using Capital Letters - ThoughtCo.](https://www.thoughtco.com/guidelines-for-using-capital-letters-1691724)
- [Letter case - Wikipedia](https://en.wikipedia.org/wiki/Letter_case)
- [Punctuation - Oxford Dictionaries](https://en.oxforddictionaries.com/grammar/punctuation)
- [Punctuation - The Purdue OWL](https://owl.english.purdue.edu/owl/section/1/6/)
- [How to Use English Punctuation Correctly - wikiHow](https://www.wikihow.com/Use-English-Punctuation-Correctly)
- [格式 - openSUSE](https://zh.opensuse.org/index.php?title=Help:%E6%A0%BC%E5%BC%8F)
- [全形和半形 - 维基百科](https://zh.wikipedia.org/wiki/%E5%85%A8%E5%BD%A2%E5%92%8C%E5%8D%8A%E5%BD%A2)
- [引号 - 维基百科](https://zh.wikipedia.org/wiki/%E5%BC%95%E8%99%9F)
- [疑问惊叹号 - 维基百科](https://zh.wikipedia.org/wiki/%E7%96%91%E5%95%8F%E9%A9%9A%E5%98%86%E8%99%9F)
