import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/performance/src"
P = "java/workbench/performance/l02"
K = "kotlin/workbench/performance/l02"
read = lambda p: (ROOT / p).read_text()
DEMO = "./gradlew :performance:demo -Pmain=workbench.performance.l02."

def demo(name):
    return {"lang": "java", "title": f"{name}.java", "src": read(f"{lab}/demo/{P}/{name}.java"),
            "run": DEMO + name, "file": f"{lab}/demo/{P}/{name}.java",
            "alt": {"lang": "kotlin", "title": f"{name}.kt", "src": read(f"{lab}/demo/{K}/{name}.kt"),
                    "run": DEMO + name + "Kt", "file": f"{lab}/demo/{K}/{name}.kt"}}

FIG = """<svg viewBox="0 0 680 250" role="img" aria-label="Cycle: the interpreter hands hot code to C1 with profiling, then to C2 with guards. When a guard fails, an uncommon trap deoptimizes the frame, the code is made not entrant, and the method is profiled and compiled again.">
<rect class="box" x="20" y="40" width="150" height="56" rx="8"/>
<text class="t" x="95" y="64" text-anchor="middle">interpreter</text>
<text class="t-s t-m" x="95" y="84" text-anchor="middle">tier 0, counts</text>
<rect class="box" x="255" y="40" width="170" height="56" rx="8"/>
<text class="t" x="340" y="64" text-anchor="middle">C1 + profile</text>
<text class="t-s t-m" x="340" y="84" text-anchor="middle">tier 3, records types</text>
<rect class="box-a" x="510" y="40" width="150" height="56" rx="8"/>
<text class="t" x="585" y="64" text-anchor="middle">C2 code</text>
<text class="t-s t-m" x="585" y="84" text-anchor="middle">tier 4, with guards</text>
<line class="ln-a" x1="170" y1="68" x2="253" y2="68" marker-end="url(#arr)"/>
<text class="t-s" x="212" y="58" text-anchor="middle">~200 calls</text>
<line class="ln-a" x1="425" y1="68" x2="508" y2="68" marker-end="url(#arr)"/>
<text class="t-s" x="467" y="58" text-anchor="middle">~5,000 more</text>
<rect class="box-bad" x="510" y="170" width="150" height="56" rx="8"/>
<text class="t" x="585" y="194" text-anchor="middle">uncommon trap</text>
<text class="t-s t-m" x="585" y="214" text-anchor="middle">a wallet arrives</text>
<line class="ln-bad" x1="585" y1="96" x2="585" y2="168" marker-end="url(#arr)"/>
<text class="t-s t-bad" x="594" y="137">guard fails</text>
<rect class="box-dim" x="255" y="170" width="170" height="56" rx="8"/>
<text class="t" x="340" y="194" text-anchor="middle">made not entrant</text>
<text class="t-s t-m" x="340" y="214" text-anchor="middle">frame goes back</text>
<line class="ln-bad" x1="510" y1="198" x2="427" y2="198" marker-end="url(#arr)"/>
<text class="t-s" x="468" y="188" text-anchor="middle">deoptimize</text>
<path class="ln-d" d="M255 198 L95 198 L95 98" marker-end="url(#arr)"/>
<text class="t-s" x="175" y="218" text-anchor="middle">re-profile, recompile</text>
</svg>"""

GUARD_J = """static long requireAmount(long cents) {
    if (cents <= 0 || cents > MAX_CENTS) throw badAmount(cents);   // hot path: 21 bytes
    return cents;
}

static IllegalArgumentException badAmount(long cents) {            // cold path, its own method
    return new IllegalArgumentException(
            String.format("amount must be between 1 and %d cents, got %d", MAX_CENTS, cents));
}"""
GUARD_K = """fun requireAmount(cents: Long): Long {
    if (cents <= 0 || cents > MAX_CENTS) throw badAmount(cents)    // hot path: 21 bytes
    return cents
}

fun badAmount(cents: Long) =                                        // cold path, its own function
    IllegalArgumentException("amount must be between 1 and %d cents, got %d".format(MAX_CENTS, cents))"""

L = {
 "id": "perf-02",
 "title": "Inlining, deoptimization and intrinsics",
 "minutes": 38,
 "goal": "By the end you can read C2's inlining and deoptimization decisions, say why a third type at a call site or a cold error path changes speed, and keep a hot method inside the inlining budget.",
 "warmup": {
  "q": "A hot loop calls `rule.fee(amount)`. For weeks only `CardFee` and `SepaFee` reach that call. Then a `WalletFee` starts taking a third of the traffic. What does C2 most likely do with that call site?",
  "options": [
   "Nothing changes: the compiled code already handles any `FeeRule`",
   "It throws the compiled code away and recompiles the call as a plain virtual call, with nothing inlined",
   "It inlines all three implementations, because they are small",
   "It stops compiling the method and leaves it in the interpreter for good"
  ],
  "answer": 1,
  "why": "C2 inlined the two types it had seen behind type checks, and compiled \"any other type\" as an uncommon trap. The first wallet trips the trap, the code is made not entrant, and the recompile sees three types with no 90% winner. That is a megamorphic site: a virtual call each time. It still works, just without inlining."
 },
 "sections": [
  {
   "h": "Inlining copies the callee into the caller, inside a bytecode budget",
   "body": "**Inlining** means C2 pastes the body of a called method into the caller and compiles them as one piece. Saving the call is the small win. The big win is that C2's other optimizations work inside one compiled unit, and now they can see both sides of the call: escape analysis (proving an object never leaves the method, so it needn't be allocated on the heap), constant folding (computing results from known values at compile time) and loop optimizations such as unrolling. A method that isn't inlined is a wall C2 can't see through.\n\nC2 decides per **call site** (one call instruction in the bytecode), using the callee's bytecode size (the `(N bytes)` from lesson 1). The rule in HotSpot's `bytecodeInfo.cpp` is short. C2 divides how often the call site ran by how often the caller was invoked. If the call runs on at least 25% of the caller's invocations (`InlineFrequencyRatio`), the site counts as hot and the limit is 325 bytes (`FreqInlineSize`). Otherwise the limit is 35 bytes (`MaxInlineSize`). There is also a depth limit of 15 levels, and a callee that is already compiled into more than 2,500 bytes of machine code (`InlineSmallCode`) is refused. These values are the same from JDK 21 to JDK 27.\n\nThe budget counts every byte, including code that almost never runs. Here is a guard that checks an amount on every refund. It builds its error message inline:\n\n```java\nstatic long requireAmountInline(long cents) {\n    if (cents <= 0 || cents > MAX_CENTS) {\n        throw new IllegalArgumentException(\n                String.format(\"amount must be between 1 and %d cents, got %d\", MAX_CENTS, cents));\n    }\n    return cents;\n}\n```\n\n```kotlin\nfun requireAmountInline(cents: Long): Long {\n    if (cents <= 0 || cents > MAX_CENTS) {\n        throw IllegalArgumentException(\"amount must be between 1 and %d cents, got %d\".format(MAX_CENTS, cents))\n    }\n    return cents\n}\n```\n\nThe Java version is 49 bytes. Move the message into its own method and the hot method shrinks to 21:\n\n```java\n" + GUARD_J + "\n```\n\n```kotlin\n" + GUARD_K + "\n```\n\nIn the demo below, each guard runs on 1 call in 8, so neither site is hot. This is the real C2 output:\n\n```text\n@ 15   ...InliningDemo::requireAmountInline (49 bytes)   too big\n@ 30   ...InliningDemo::requireAmountSplit (21 bytes)   inline (hot)\n```\n\nDon't read too much into `inline (hot)`. It's simply the message C2 prints when it inlines and has nothing more specific to say. The JDK's own code uses this split all the time: a small check, and a separate method that builds the exception.",
   "try": {
    "title": "See C2 refuse the big guard",
    "minutes": 4,
    "steps": [
     "Run `InliningDemo`. It starts a second JVM with `-XX:+UnlockDiagnosticVMOptions -XX:+PrintInlining` and keeps the lines about `refund`.",
     "Find the decisions under the tier 3 compile (C1 says `callee is too large`) and under the tier 4 compile (C2 says `too big`).",
     "Run the Kotlin twin. Compare the size of `requireAmountInline` in both languages."
    ],
    "code": demo("InliningDemo"),
    "expect": "Both compilers refuse `requireAmountInline` and inline `requireAmountSplit`. In Java the sizes are 49 and 21 bytes. In Kotlin the inline-message version is 66 bytes: Kotlin's `\"...\".format(...)` is an `inline` function, so kotlinc pastes its body (an array copy and a null check) into the caller. The split version is 21 bytes in both."
   },
   "refs": [
    {"title": "bytecodeInfo.cpp: C2's inlining rules (JDK 25)", "url": "https://github.com/openjdk/jdk/blob/jdk-25-ga/src/hotspot/share/opto/bytecodeInfo.cpp", "kind": "read"}
   ]
  },
  {
   "h": "C2 bets on the receiver types it has seen",
   "body": "A call through an interface, like `rule.fee(amount)`, could go to any implementation. C2 can only inline it if it knows which one. The object a method is called on is the **receiver**, so at tier 3 C1 records the receiver types it sees at every call site, and C2 reads that profile.\n\nOne type seen: C2 inlines that type's method behind a cheap class check. This is a monomorphic call site. Two types: it inlines both behind two checks (bimorphic). The profile keeps two types per site (`TypeProfileWidth` = 2). With three or more, C2 inlines only a type that has at least 90% of the calls (`TypeProfileMajorReceiverPercent`). Otherwise the site is **megamorphic**: C2 emits a plain virtual call (look up the method in the receiver's class at run time, then jump to it) and inlines nothing.\n\n`-XX:+PrintInlining` shows the switch. These are real lines for the `area()` call in lesson 1's `Hot` program, before and after the new shapes arrived:\n\n```text\n@ 27   Hot$Square::area (10 bytes)   inline (hot)\n \\-> TypeProfile (977323/977323 counts) = Hot$Square\n\n@ 27   Hot$Shape::area (0 bytes)   virtual call\n```\n\nThe cost is more than the call. `MegamorphicBench` feeds one call site with 1, 2 or 3 fee-rule types, in batches of 1,024. In several runs on the shared 4-vCPU VM used for this course, one type took 0.2 to 0.4 µs per batch, two types 0.4 to 0.7 µs, and three types 3 to 4 µs. The error bars were wide on that noisy machine, but the jump at three types showed up in every run. With the calls inlined, C2 can optimize the whole loop. With a virtual call per element, it can't.\n\nNotice what didn't matter. The fee-rule classes in the benchmark are `final`, and so are the records in `Hot`. C2 inlined `Square::area` because the profile said every receiver was a `Square`, not because of a modifier. Kotlin classes are final by default, and that doesn't change anything here either. What changes speed is how many types reach one call site.",
   "try": {
    "title": "Count the types at a call site",
    "minutes": 5,
    "steps": [
     "Predict the three numbers before you run: ns per batch with 1, 2 and 3 types.",
     "Run `MegamorphicBench`. It's a JMH benchmark (lesson 3 explains JMH). Each case runs in a fresh JVM, so each starts with a clean profile. It takes about 10 seconds.",
     "Run it with `-Pargs='1 4'`. Does a fourth type cost more than the third? The Kotlin twin runs 1, 3 and 4 types."
    ],
    "code": demo("MegamorphicBench"),
    "expect": "One and two types are close, both a few hundred nanoseconds per batch. Three types cost several times more, around ten times on the course VM. Four types cost about the same as three: once the site is megamorphic, it's a virtual call either way. Expect wide error bars on a laptop with other work running."
   }
  },
  {
   "h": "When a bet loses: uncommon traps and deoptimization",
   "body": "C2 compiles what the profile showed and nothing else. A branch that was never taken and a receiver type that never appeared don't get compiled code. In their place C2 puts an **uncommon trap**: a stub that hands the running frame back to the interpreter if that \"impossible\" case ever happens.\n\nWhen a trap fires, the JVM **deoptimizes**: it rebuilds an interpreter frame from the compiled frame and carries on there. The compiled code is made not entrant. The method goes back to profiling, now with the new case in its profile, and gets compiled again. The figure shows the cycle.\n\n`DeoptDemo` triggers both common kinds. It settles batches of card charges, then one refund appears, then SEPA and wallet payments arrive:\n\n```java\nlong fee = methods[i].feeCents(amounts[i]);   // bytecode 20: which types has it seen?\nif (refund[i]) net -= amounts[i];             // bytecode 31: has this branch ever been taken?\nelse net += amounts[i] - fee;\n```\n\n```kotlin\nval fee = methods[i].feeCents(amounts[i])     // which types has it seen?\nif (refund[i]) net -= amounts[i]              // has this branch ever been taken?\nelse net += amounts[i] - fee\n```\n\nThe real log on JDK 25, trimmed to the important parts:\n\n```text\nphase 2: one refund per batch\n... DeoptDemo.settle(...) trap_bci=31 unstable_if reinterpret\n81   23       4       ...DeoptDemo::settle (62 bytes)   made not entrant: uncommon trap\nphase 3: SEPA and wallet payments arrive\n... DeoptDemo.settle(...) trap_bci=20 class_check maybe_recompile\n93   25       4       ...DeoptDemo::settle (62 bytes)   made not entrant: uncommon trap\n```\n\n`unstable_if` means a branch C2 had compiled as never taken: the refund. `class_check` means a type check failed at a call it had inlined for cards only. Each time, a new tier 4 compile follows within a few milliseconds.\n\nThis is normal, and cheap when it happens a few times. HotSpot also limits how often one method can go around the cycle (`PerMethodRecompilationCutoff` is 400 recompiles). Expect a burst of deoptimizations after a deploy, or when a new payment method gets its first traffic. A steady stream of them in a service that has been up for hours is worth a look. JFR has a ready-made view for it, `deoptimizations-by-reason`, which lesson 5 uses.",
   "figure": {"svg": FIG, "caption": "C2 compiles only what the profile saw. An unseen case hits an uncommon trap, the code is retired, and the method is profiled and compiled again."},
   "try": {
    "title": "Trip a branch trap and a type trap",
    "minutes": 4,
    "steps": [
     "Predict: in which phase will the first `made not entrant` for tier 4 code appear, and with which reason in the deoptimization log?",
     "Run `DeoptDemo`. It starts a second JVM with `-XX:+PrintCompilation -Xlog:deoptimization=debug`.",
     "Match each `trap_bci` to a line of `settle` (bytecode 20 is the `feeCents` call, 31 is the `if (refund[i])` test). Then run the Kotlin twin: its bytecode indexes differ, the story doesn't."
    ],
    "code": demo("DeoptDemo"),
    "expect": "Phase 1 compiles `settle` up to tier 4, including an OSR version. Phase 2 prints `unstable_if` at `trap_bci=31` and retires the tier 4 code, then recompiles. Phase 3 prints `class_check` at `trap_bci=20`, retires it again and recompiles. On JDK 25 the PrintCompilation lines end in `made not entrant: uncommon trap`; on JDK 21 they just say `made not entrant`."
   }
  },
  {
   "h": "Intrinsics: JDK methods the JIT swaps for hand-written code",
   "body": "Some JDK methods never run as their Java code once they're hot. HotSpot has hand-written machine code, or hand-written compiler IR (the compiler's internal form of a program), for them. These are **intrinsics**. In the JDK source they carry `@IntrinsicCandidate`, whose Javadoc says the method \"may be (but is not guaranteed to be) intrinsified\". `PrintInlining` marks them:\n\n```text\njava.lang.Long::bitCount (61 bytes)   (intrinsic)\njava.lang.Math::addExact (32 bytes)   (intrinsic)\njava.util.Arrays::equals (43 bytes)   (intrinsic)\n```\n\nThose are real lines from `IntrinsicsDemo`. `Long.bitCount` is 61 bytes of shifts and masks in Java, and on x86 C2 replaces it with one `POPCNT` instruction. `Arrays.equals` on byte arrays ends up in `ArraysSupport.vectorizedMismatch`, which reads 8 bytes at a time even in its Java version, and is an intrinsic as well. The bytecode size doesn't matter for an intrinsic, because that Java code isn't what runs.\n\nThe practical rule: in hot code, call the JDK method instead of writing the loop yourself. For money in cents, `Math.addExact` and `Math.multiplyExact` give you overflow checks that throw `ArithmeticException`, and both are intrinsics. A hand-written loop that compares two idempotency keys byte by byte gives up the 8-bytes-at-a-time path that `Arrays.equals` gets for free, and it's more code to get wrong.\n\nKotlin gets the same intrinsics, because its standard library calls these JDK methods. `ByteArray.contentEquals` calls `java.util.Arrays.equals`, and `Long.countOneBits()` calls `java.lang.Long.bitCount`:\n\n```java\nlong total = Math.addExact(a, b);                 // ArithmeticException on overflow\nboolean same = Arrays.equals(keyA, keyB);\nint flags = Long.bitCount(riskMask);\n```\n\n```kotlin\nval total = Math.addExact(a, b)                   // ArithmeticException on overflow\nval same = keyA.contentEquals(keyB)               // calls java.util.Arrays.equals\nval flags = riskMask.countOneBits()               // calls java.lang.Long.bitCount\n```",
   "try": {
    "title": "List the intrinsics in a hot loop",
    "minutes": 3,
    "steps": [
     "Run `IntrinsicsDemo`. It prints the `PrintInlining` lines for the three JDK methods it calls.",
     "Run the Kotlin twin, which uses `contentEquals` and `countOneBits` instead of calling `Arrays` and `Long` directly.",
     "Optional: run the Java demo's child JVM yourself with `-XX:+PrintInlining` and grep for `intrinsic` to see how many others the JDK uses on its own."
    ],
    "code": demo("IntrinsicsDemo"),
    "expect": "Both programs print the same three lines, each ending in `(intrinsic)`: `Long::bitCount`, `Math::addExact` and `Arrays::equals`. Kotlin's standard library functions disappear entirely: they are `inline`, so the call in the bytecode is already the JDK method."
   }
  }
 ],
 "analogy": "Think of a routing switch at a payment processor. If almost every transaction it has seen is Visa, it keeps a fast lane wired straight to the Visa network and sends anything else to a slow manual desk. Two networks still fit: two fast lanes. When it has seen five networks with no clear winner, it stops keeping fast lanes and looks up each transaction's route in a table. That's a megamorphic call site. When the first Amex arrives at a switch wired only for Visa, it goes to the manual desk, and the switch gets rewired with Amex in mind (an uncommon trap, then a recompile). The analogy breaks on cost: a real switch pays for each manual review, while the JVM pays once per trap and then rebuilds the fast path.",
 "in_your_world": "Payment code is full of interfaces with a handful of implementations: `PaymentMethod`, `FeeRule`, `RiskCheck`, Kafka `Deserializer`s. When a hot loop in your settlement job calls through one of them and three or more implementations reach the same call site, that call becomes a virtual call and the loop around it loses its optimizations. You won't see that in a code review. You'll see it in a profile (lessons 5 and 6) or in a JMH run. Also expect a short burst of deoptimizations when a new payment method goes live, since the first wallet payment trips traps compiled for cards only. That burst is fine. A steady stream hours later is a signal to check `jfr view deoptimizations-by-reason`.",
 "mistake": "The common mistake is adding `final` to classes and methods to make calls faster. Part of the confusion is that `final` does matter for fields, as lesson 3 shows. For calls, C2 decides from the type profile. It inlined `Square::area` because every receiver it saw was a `Square`, and the third record type still turned the call into a virtual call, `final` or not. Kotlin's final-by-default classes behave the same way. If a profile shows a hot megamorphic call, measure it with JMH first. Then reduce the number of types that reach that one call site, or keep the hot callee small so it inlines wherever the type is known.",
 "compare": {
  "title": "The same guard, before and after the split",
  "java": {"title": "InliningDemo.java", "src": "// before: 49 bytes, \"too big\" at a site that isn't hot\nstatic long requireAmountInline(long cents) {\n    if (cents <= 0 || cents > MAX_CENTS) {\n        throw new IllegalArgumentException(\n                String.format(\"amount must be between 1 and %d cents, got %d\", MAX_CENTS, cents));\n    }\n    return cents;\n}\n\n// after: 21 bytes, inlined\n" + GUARD_J},
  "kotlin": {"title": "InliningDemo.kt", "src": "// before: 66 bytes, \"too big\" at a site that isn't hot\nfun requireAmountInline(cents: Long): Long {\n    if (cents <= 0 || cents > MAX_CENTS) {\n        throw IllegalArgumentException(\"amount must be between 1 and %d cents, got %d\".format(MAX_CENTS, cents))\n    }\n    return cents\n}\n\n// after: 21 bytes, inlined\n" + GUARD_K},
  "note": "After the split, both languages compile `requireAmount` to the same 21 bytes, and C2 treats them the same. Before the split, the Kotlin version is 66 bytes against Java's 49. Kotlin's `String.format` extension is an `inline` function, so kotlinc copies its body into the caller: an `Arrays.copyOf` of the arguments and a null check. Kotlin `inline` removes a call at compile time, but the pasted bytecode counts against the JIT's budget for the method that received it. Use `inline` for small higher-order functions, and keep big bodies out of hot methods in either language."
 },
 "worked": {
  "title": "Find out why a hot method isn't inlined, and fix it",
  "steps": [
   {"say": "A refund handler is slower than expected in a profile. Start the service with the diagnostic flags and look for your method in the inlining log.", "code": "java -XX:+UnlockDiagnosticVMOptions -XX:+PrintInlining -cp app.jar com.acme.pay.Main | grep requireAmount", "lang": "bash"},
   {"say": "C2's line names the method, its bytecode size and the reason. `too big` means the call site isn't hot and the callee is over 35 bytes. `hot method too big` would mean a hot site and a callee over 325 bytes.", "code": "@ 15   com.acme.pay.Guards::requireAmount (49 bytes)   too big", "lang": "text"},
   {"say": "Look at what the 49 bytes are. `javap -c -p` shows the boxing calls, the varargs array and `String.format` that build the message. All of that is the cold path.", "code": "javap -c -p -cp app.jar com.acme.pay.Guards | grep -A 30 'long requireAmount'", "lang": "bash"},
   {"say": "Move the cold path into its own method and return the exception from it, so the hot method still ends in `throw`. Self-check before reading on: why return the exception instead of throwing it inside the helper? (Answer: with `throw badAmount(cents)`, javac and the reader can see that the method ends there. A helper that throws by itself looks like an ordinary call that returns.)", "code": GUARD_J, "lang": "java", "alt_lang": "kotlin", "alt_code": GUARD_K},
   {"say": "Run the same command again. The hot method is 21 bytes and C2 inlines it. Keep the message text identical, because someone's alerting or log search may match on it.", "code": "@ 15   com.acme.pay.Guards::requireAmount (21 bytes)   inline (hot)", "lang": "text"}
  ]
 },
 "lab": {
  "title": "Fit two hot guards into the inlining budget",
  "minutes": 12,
  "files": [f"{lab}/main/{P}/PaymentGuards.java"],
  "run": "./gradlew :performance:test --tests 'workbench.performance.l02.*'",
  "steps": [
   "Run the tests. Two pass (the guards behave correctly) and two fail: `requireAmount` is 49 bytes of bytecode and `requireIdempotencyKey` is 68. The limit in the test is 35, C2's `MaxInlineSize`.",
   "Check the sizes yourself: after a build, run `javap -c -p -cp performance/build/classes/java/main workbench.performance.l02.PaymentGuards`. The offset of the last instruction plus one is the size.",
   "Move the message building out of `requireAmount` into a private static method that returns the exception. Keep the exact message.",
   "Do the same for `requireIdempotencyKey`. The `null` case must still say `got null`.",
   "Run the tests until all four pass. The test reads the compiled class file, so `BytecodeSize.java` in the test folder shows exactly what it measures."
  ],
  "hints": [
   "The shape that fits: `if (bad) throw badAmount(cents); return cents;`. Everything about the message goes in `badAmount`.",
   "`String.format` with two arguments costs a lot of bytecode: an array, two boxing calls and the call itself. In the cold method that doesn't matter.",
   "In `requireIdempotencyKey`, the `key == null ? \"null\" : ...` choice belongs in the cold method too. Pass the key itself to the helper.",
   "Both fixed methods come out at 21 and 27 bytes in the reference solution."
  ],
  "done_when": "All four tests in `PaymentGuardsTest` pass."
 },
 "drill": {
  "title": "Split a guard from memory",
  "minutes": 4,
  "prompt": "Close this page. Write a guard `requireCurrency(String code)` that returns `code` when it is exactly 3 characters long, and otherwise throws `IllegalArgumentException(\"currency must be 3 letters, got '\" + code + \"'\")`. Shape it so the hot method stays small. Then write down the two C2 size limits and when each applies.",
  "answer": {"lang": "java", "src": "static String requireCurrency(String code) {\n    if (code == null || code.length() != 3) throw badCurrency(code);   // hot: a check and a call\n    return code;\n}\n\nprivate static IllegalArgumentException badCurrency(String code) {     // cold: everything else\n    return new IllegalArgumentException(\"currency must be 3 letters, got '\" + code + \"'\");\n}\n\n// C2 inlines up to 35 bytes of bytecode at a call site that runs on fewer than 25% of the\n// caller's invocations (MaxInlineSize), and up to 325 bytes at a hot one (FreqInlineSize).",
             "alt": {"lang": "kotlin", "src": "fun requireCurrency(code: String?): String {\n    if (code == null || code.length != 3) throw badCurrency(code)      // hot: a check and a call\n    return code\n}\n\nprivate fun badCurrency(code: String?) =                               // cold: everything else\n    IllegalArgumentException(\"currency must be 3 letters, got '$code'\")\n\n// C2 inlines up to 35 bytes of bytecode at a call site that runs on fewer than 25% of the\n// caller's invocations (MaxInlineSize), and up to 325 bytes at a hot one (FreqInlineSize)."}}
 },
 "recap": [
  "C2 inlines a callee only within a bytecode budget: 35 bytes at call sites that aren't hot, 325 bytes at hot ones (25% of the caller's calls). Cold error paths count too, so give them their own method.",
  "At each interface or virtual call, C2 uses the receiver types tier 3 recorded. One or two types get inlined behind type checks. Three or more without a 90% winner become a plain virtual call.",
  "Whatever the profile never saw becomes an uncommon trap. When one fires, the frame goes back to the interpreter, the code is made not entrant, and the method is recompiled with the new case.",
  "`-XX:+UnlockDiagnosticVMOptions -XX:+PrintInlining` and `-Xlog:deoptimization=debug` show these decisions. `inline (hot)` is just C2's success message.",
  "Intrinsics (`@IntrinsicCandidate`) swap JDK methods such as `Math.addExact`, `Arrays.equals` and `Long.bitCount` for hand-written code. Kotlin's standard library reaches the same ones."
 ],
 "quiz": [
  {"q": "C2's inlining log shows `@ 15   Guards::requireAmount (49 bytes)   too big` inside a refund handler. Which change is most likely to get it inlined?",
   "options": ["Mark `requireAmount` as `final`", "Move the message building into a separate method so `requireAmount` is under 35 bytes", "Raise the heap size with `-Xmx`", "Wrap the call in a lambda"],
   "answer": 1,
   "why": "`too big` means the site isn't hot, so the 35-byte limit applies, and the cold message code is most of the 49 bytes. A static method is already statically bound, so `final` changes nothing, and the heap has nothing to do with inlining."},
  {"q": "A call site has seen `CardFee` (50%), `SepaFee` (30%) and `WalletFee` (20%). What does C2 compile there?",
   "options": ["Three inlined bodies behind three type checks", "`CardFee` inlined, the rest as a virtual call", "A plain virtual call, with nothing inlined", "Nothing: the method stays at tier 3"],
   "answer": 2,
   "why": "The profile holds two types per site, and with more than that C2 needs one type with at least 90% of the calls to inline it. 50% isn't enough, so the site is megamorphic and becomes a virtual call."},
  {"q": "A deoptimization log line reads `trap_bci=31 unstable_if reinterpret`. What happened?",
   "options": ["Bytecode 31 is a branch C2 compiled as never taken; it was taken, so the frame went back to the interpreter and the method will be recompiled", "The JVM ran out of code cache at bytecode 31", "A class was loaded twice", "The method threw an exception at bytecode 31"],
   "answer": 0,
   "why": "`unstable_if` is the trap C2 places on a branch the profile never saw taken. When it runs, the JVM deoptimizes the frame and the code is made not entrant. `class_check` would be the type-based version."},
  {"q": "The inlining log shows `java.lang.Long::bitCount (61 bytes)   (intrinsic)`. What does that tell you?",
   "options": ["The method was too big to inline", "C2 replaced the call with hand-written code, so the 61 bytes of Java don't run in that compiled code", "The method was compiled to 61 bytes of machine code", "The method runs in the interpreter"],
   "answer": 1,
   "why": "An intrinsic replaces the method body with code HotSpot ships for it, a single POPCNT on x86 for `bitCount`. The size in the line is still the Java bytecode size, which is irrelevant once the intrinsic applies."},
  {"q": "PrintCompilation shows `DeoptDemo::settle (62 bytes)`. Using what lesson 1 said about that number, can C2 inline `settle` into a caller that calls it on only 1 invocation in 10?",
   "options": ["Yes, 62 bytes of machine code is small", "No: 62 bytes of bytecode is over the 35-byte limit for a site that isn't hot", "Yes, any method under 325 bytes is always inlined", "No, methods with loops are never inlined"],
   "answer": 1,
   "why": "`(62 bytes)` is the bytecode size. A call on 1 invocation in 10 is below the 25% bar, so the 35-byte `MaxInlineSize` applies and 62 is too big. At a hot site the limit would be 325 and it could be inlined.",
   "from": "perf-01"}
 ],
 "flashcards": [
  {"front": "Biggest callee (in bytecode) that C2 inlines at a call site it doesn't consider hot?", "back": "35 bytes (`MaxInlineSize`)."},
  {"front": "When does C2 treat a call site as hot, and what's the size limit there?", "back": "When the call runs on at least 25% of the caller's invocations. Then the limit is 325 bytes (`FreqInlineSize`)."},
  {"front": "How many receiver types does C2 inline at one call site from the profile?", "back": "Up to two. With more, only a type with at least 90% of the calls; otherwise it emits a virtual call (megamorphic)."},
  {"front": "What is an uncommon trap?", "back": "A stub C2 puts where the profile saw nothing, such as an untaken branch or an unseen type. If it runs, the frame is deoptimized and the code is made not entrant."},
  {"front": "Does marking a class `final` make calls to it faster in C2?", "back": "Not by itself. C2 inlines from the receiver-type profile. What matters is how many types reach the call site."},
  {"front": "What does `@IntrinsicCandidate` on a JDK method mean?", "back": "HotSpot may replace the method with hand-written machine code or compiler IR, as it does for `Math.addExact` and `Arrays.equals`."},
  {"front": "Why can a Kotlin function be bigger in bytecode than the same Java code?", "back": "Calls to Kotlin `inline` functions, such as `\"...\".format(x)`, are pasted into the caller by kotlinc, and that bytecode counts against the JIT's inlining budget."}
 ],
 "terms": [
  {"term": "Inlining", "plain": "Pasting a called method's body into the caller so C2 compiles and optimizes them together."},
  {"term": "Call site", "plain": "One specific call instruction in the bytecode. Profiles and inlining decisions are per call site."},
  {"term": "Monomorphic, bimorphic, megamorphic", "plain": "One, two, or too many receiver types seen at a call site."},
  {"term": "Type profile", "plain": "The receiver types and counts that tier 3 records at each call site."},
  {"term": "Uncommon trap", "plain": "A stub in C2 code for a case the profile never saw. Running it deoptimizes the frame."},
  {"term": "Deoptimization", "plain": "Turning a compiled frame back into an interpreter frame and retiring the compiled code."},
  {"term": "Intrinsic", "plain": "A JDK method that HotSpot replaces with its own hand-written code."}
 ],
 "explain_back": {
  "prompt": "A colleague asks: \"Why did our settlement loop get slower when we added a third payment method, even though the new class is tiny?\" Explain it in your own words.",
  "answer": "The loop calls `feeCents` through the `PaymentMethod` interface. While only cards and SEPA reached that call, C2 inlined both implementations behind type checks, and could then optimize the loop body as a whole. It compiled any other type as an uncommon trap. When the first wallet payment arrived, the trap fired, the compiled code was thrown away and the method was recompiled. With three types and none above 90%, the call site is megamorphic, so C2 now emits a virtual call for every element and inlines nothing. The size of the new class doesn't matter. What changed is the number of types reaching that one call."
 },
 "deeper": {
  "minutes": 10,
  "body": "Inlining is what makes escape analysis work. C2 can only prove that an object never leaves a method if it can see every method the object is passed to. A `Money` value created in a hot method and passed to a callee that isn't inlined has escaped, so it gets allocated on the heap. The memory track looks at escape analysis from the allocation side.\n\nFor experiments, `-XX:CompileCommand=dontinline,com.acme.pay.Guards::requireAmount` and `-XX:CompileCommand=inline,...` force a decision for one method, and the inlining log says `force inline by CompileCommand`. Use them to test a theory, not as a production fix.\n\nOne result here surprised me. I expected a shared helper such as `static long timed(LongSupplier work)` to make its `work.getAsLong()` call megamorphic when three different lambdas pass through it. C2 inlined all three anyway. Once it had inlined `timed` into each caller, it knew the exact lambda class at each spot and didn't need the shared profile. Megamorphic sites come from types that C2 can't see at compile time, such as objects read from an array, a field or a collection.\n\nOther messages you'll meet in the log: `inlining too deep` (more than 15 levels, `MaxInlineLevel`), `already compiled into a big method` (a callee already compiled into more than 2,500 bytes of machine code), `hot method too big` (a hot site, over 325 bytes) and `no static binding` (C1 can't inline a virtual call). JITWatch shows the same information per method if the raw log gets too long."
 },
 "sources": [
  {"title": "bytecodeInfo.cpp: C2's inlining rules and messages (JDK 25)", "url": "https://github.com/openjdk/jdk/blob/jdk-25-ga/src/hotspot/share/opto/bytecodeInfo.cpp"},
  {"title": "c2_globals.hpp: MaxInlineSize, FreqInlineSize and other C2 defaults (JDK 25)", "url": "https://github.com/openjdk/jdk/blob/jdk-25-ga/src/hotspot/share/opto/c2_globals.hpp"},
  {"title": "IntrinsicCandidate.java: what the annotation means (JDK 25)", "url": "https://github.com/openjdk/jdk/blob/jdk-25-ga/src/java.base/share/classes/jdk/internal/vm/annotation/IntrinsicCandidate.java"},
  {"title": "Inline functions (Kotlin documentation)", "url": "https://kotlinlang.org/docs/inline-functions.html"}
 ]
}
out = ROOT / "content/lessons/perf-02.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
