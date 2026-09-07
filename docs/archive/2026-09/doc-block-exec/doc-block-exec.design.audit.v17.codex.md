## Summary
The design is otherwise coherent with the supplied spec: its API, lifecycle/cleanup precedence, CLI partition, mutation plan, and migration wire all cover the stated requirements. Axis C reconciliation follows; AC-1.6 is restated incompletely because the scanner calls itself CommonMark-aware but omits CommonMark's opening-fence indentation boundary.

| Spec AC | Classification |
|---|---|
| AC-1.1 | implemented-as-written |
| AC-1.2 | implemented-as-written |
| AC-1.3 | implemented-as-written |
| AC-1.4 | implemented-as-written |
| AC-1.5 | implemented-as-written |
| AC-1.6 | restated |
| AC-1.7 | implemented-as-written |
| AC-1.8 | implemented-as-written |
| AC-1.9 | implemented-as-written |
| AC-2.1 | implemented-as-written |
| AC-2.2 | implemented-as-written |
| AC-2.3 | implemented-as-written |
| AC-2.4 | implemented-as-written |
| AC-2.5 | implemented-as-written |
| AC-2.6 | implemented-as-written |
| AC-2.7 | implemented-as-written |
| AC-2.8 | implemented-as-written |
| AC-3.1 | implemented-as-written |
| AC-3.2 | implemented-as-written |
| AC-3.3 | implemented-as-written |
| AC-3.4 | implemented-as-written |
| AC-3.5 | implemented-as-written |
| AC-3.6 | implemented-as-written |
| AC-3.7 | implemented-as-written |
| AC-3.8 | implemented-as-written |
| AC-3.9 | implemented-as-written |
| AC-3.10 | implemented-as-written |
| AC-3.11 | implemented-as-written |
| AC-3.12 | implemented-as-written |
| AC-3.13 | implemented-as-written |
| AC-3.14 | implemented-as-written |
| AC-4.1 | implemented-as-written |
| AC-4.2 | implemented-as-written |
| AC-4.3 | implemented-as-written |
| AC-4.4 | implemented-as-written |
| AC-4.5 | implemented-as-written |
| AC-4.6 | implemented-as-written |
| AC-5.1 | implemented-as-written |
| AC-5.2 | implemented-as-written |
| AC-5.3 | implemented-as-written |
| AC-5.4 | implemented-as-written |
| AC-5.5 | implemented-as-written |
| AC-5.6 | implemented-as-written |
| AC-6.1 | implemented-as-written |
| AC-6.2 | implemented-as-written |
| AC-6.3 | implemented-as-written |
| AC-6.4 | implemented-as-written |
| AC-6.5 | implemented-as-written |
| AC-6.6 | implemented-as-written |

## Must-fix
- AC-1.6 is only partially specified: the spec requires a tag inside a *fence body* to be inert and says the parser follows CommonMark fences, whereas the design says merely that an opener records its “leading run” and gives no 0–3-space indentation rule. Under CommonMark, a line indented by four spaces is an indented code block, not a fence; the proposed scanner can therefore select and execute `    ```bash hmad:exec` as if it were an opt-in fence. Define opening/closing indentation semantics (at minimum, reject openers indented four or more spaces) and add a hostile fixture proving that an indented literal tag is never a candidate. This is a narrower restatement of AC-1.6's fence-body/security boundary and must be resolved in the spec or design before implementation.

## Should-fix
None

## Nit
None
