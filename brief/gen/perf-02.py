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

def pair(java, kotlin):
    """A Java fence and its Kotlin twin, side by side, as the validator expects."""
    return f"```java\n{java}\n```\n\n```kotlin\n{kotlin}\n```"

FIG = """<svg viewBox="0 0 680 250" role="img" aria-label="Cycle: the interpreter hands busy code to C1 with profiling, then to C2 with type checks. When a check fails, an uncommon trap deoptimizes the call, the code is made not entrant, and the method is profiled and compiled again.">
<rect class="box" x="20" y="40" width="150" height="56" rx="8"/>
<text class="t" x="95" y="64" text-anchor="middle">interpreter</text>
<text class="t-s t-m" x="95" y="84" text-anchor="middle">tier 0, counts</text>
<rect class="box" x="255" y="40" width="170" height="56" rx="8"/>
<text class="t" x="340" y="64" text-anchor="middle">C1 + profile</text>
<text class="t-s t-m" x="340" y="84" text-anchor="middle">tier 3, records types</text>
<rect class="box-a" x="510" y="40" width="150" height="56" rx="8"/>
<text class="t" x="585" y="64" text-anchor="middle">C2 code</text>
<text class="t-s t-m" x="585" y="84" text-anchor="middle">tier 4, with checks</text>
<line class="ln-a" x1="170" y1="68" x2="253" y2="68" marker-end="url(#arr)"/>
<text class="t-s" x="212" y="58" text-anchor="middle">~200 calls</text>
<line class="ln-a" x1="425" y1="68" x2="508" y2="68" marker-end="url(#arr)"/>
<text class="t-s" x="467" y="58" text-anchor="middle">~5,000 more</text>
<rect class="box-bad" x="510" y="170" width="150" height="56" rx="8"/>
<text class="t" x="585" y="194" text-anchor="middle">uncommon trap</text>
<text class="t-s t-m" x="585" y="214" text-anchor="middle">a heading arrives</text>
<line class="ln-bad" x1="585" y1="96" x2="585" y2="168" marker-end="url(#arr)"/>
<text class="t-s t-bad" x="594" y="137">check fails</text>
<rect class="box-dim" x="255" y="170" width="170" height="56" rx="8"/>
<text class="t" x="340" y="194" text-anchor="middle">made not entrant</text>
<text class="t-s t-m" x="340" y="214" text-anchor="middle">call goes back</text>
<line class="ln-bad" x1="510" y1="198" x2="427" y2="198" marker-end="url(#arr)"/>
<text class="t-s" x="468" y="188" text-anchor="middle">deoptimize</text>
<path class="ln-d" d="M255 198 L95 198 L95 98" marker-end="url(#arr)"/>
<text class="t-s" x="175" y="218" text-anchor="middle">re-profile, recompile</text>
</svg>"""

INLINE_J = """static long requireWordCountInline(long words) {
    if (words <= 0 || words > MAX_WORDS) {
        throw new IllegalArgumentException(
                String.format("word count must be between 1 and %d, got %d", MAX_WORDS, words));
    }
    return words;
}"""
INLINE_K = """fun requireWordCountInline(words: Long): Long {
    if (words <= 0 || words > MAX_WORDS) {
        throw IllegalArgumentException("word count must be between 1 and %d, got %d".format(MAX_WORDS, words))
    }
    return words
}"""
GUARD_J = """static long requireWordCount(long words) {
    if (words <= 0 || words > MAX_WORDS) throw badWordCount(words);   // hot path: 21 bytes
    return words;
}

static IllegalArgumentException badWordCount(long words) {           // cold path, its own method
    return new IllegalArgumentException(
            String.format("word count must be between 1 and %d, got %d", MAX_WORDS, words));
}"""
GUARD_K = """fun requireWordCount(words: Long): Long {
    if (words <= 0 || words > MAX_WORDS) throw badWordCount(words)    // hot path: 21 bytes
    return words
}

fun badWordCount(words: Long) =                                        // cold path, its own function
    IllegalArgumentException("word count must be between 1 and %d, got %d".format(MAX_WORDS, words))"""

OPENING = """Back in the kitchen, the cook knows the house favourites by heart now, thanks to two habits. When a recipe says "make the sauce on page 12", the cook copies the sauce into the main recipe, so the onions for both get chopped at once. And when nearly every customer wants fries, a basket of fries waits by the stove.

C2 has both habits. It copies small methods into their callers, and it bets on the types that usually show up at a call. Then a customer asks for rice, the bet is lost, and the cook is back at the recipe card. Lesson 1 caught exactly that: `readingMillis` thrown away with `made not entrant: uncommon trap` when headings arrived.

None of this shows in your source, so it's easy to miss: a third kind of block, or a long error message, can change the speed of code that looks the same. In this lesson, we'll watch C2 copy one method and refuse another, count the types at a call, trip its bets on purpose, and meet the JDK methods it swaps for ready-made machine code. Before we start, make a guess, and keep it in mind."""

# ---------------------------------------------------------------- section 0
S0 = """Start with something you can see. The report service checks every document it receives, and here's one check, written the way most of us would write it the first time:

""" + pair(INLINE_J, INLINE_K) + """

It looks tiny. C2 disagrees: it's 49 bytes of bytecode, and that number decides whether C2 will copy it into its callers.

**Inlining** means C2 pastes the body of a called method into the caller and compiles the two as one piece. It's the cook copying the sauce recipe from page 12 into the main recipe. Skipping the call itself is the small win. The big win is that C2's other optimizations can now see both sides of the call. Escape analysis can prove that an object never leaves the method, so it needn't be put on the heap at all. Constant folding can work out results from values known at compile time. Loop optimizations, such as unrolling (copying the loop body a few times so the loop makes fewer laps), can work on the whole loop. A method C2 doesn't inline is a wall it can't see through.

C2 decides at each **call site**, one call instruction in the bytecode, using the callee's bytecode size: the `(N bytes)` from lesson 1. The rule in HotSpot's `bytecodeInfo.cpp` is short. If the call runs on at least 25% of the caller's invocations (`InlineFrequencyRatio`), the site counts as hot, and C2 inlines methods of up to 325 bytes (`FreqInlineSize`). Otherwise the limit is 35 bytes (`MaxInlineSize`). C2 also stops 15 levels deep (`MaxInlineLevel`), and it refuses a callee that is already compiled into more than 2,500 bytes of machine code (`InlineSmallCode`). These values are the same from JDK 21 to JDK 27.

The budget counts every byte, even code that almost never runs. Most of the check's 49 bytes build the error message: two boxing calls, which wrap each `long` in a `Long` object, an array for the arguments, and `String.format`. Move that cold path into its own method and the hot method shrinks to 21 bytes:

""" + pair(GUARD_J, GUARD_K) + """

`InliningDemo` calls both versions from a method called `summarize`, each on 1 call in 8, so neither call site is hot. This is the real C2 output on JDK 25:

```text
@ 15   ...InliningDemo::requireWordCountInline (49 bytes)   failed to inline: too big
@ 30   ...InliningDemo::requireWordCountSplit (21 bytes)   inline (hot)
```

JDK 21 prints the same decisions without the `failed to inline:` prefix. Don't read too much into `inline (hot)`, by the way. It's simply what C2 prints when it inlines and has nothing more specific to say. The JDK's own code uses this split all the time: a small check, plus a separate method that builds the exception.

**C2 counts the bytes of the error path too. Give the cold path its own method.**

This check is a static method, so C2 always knows which code a call to it runs. Most calls in an object-oriented program aren't so simple."""

ASIDE = {
 "title": "Is Kotlin's inline the same thing?",
 "body": "No, though the two are related. Kotlin's `inline` keyword makes kotlinc copy a function's body into each caller while it compiles your source, before the JVM ever sees it. C2's inlining happens later, at run time, and only for calls it judges small or hot enough. The two add up: bytecode that kotlinc pasted in counts against C2's budget for the method that received it. That's why the Kotlin check above is 66 bytes, because `\"...\".format(...)` is an inline function that brings an array copy and a null check with it. Use `inline` for small functions that take lambdas, where it saves an object per call, and keep big bodies out of hot methods in either language."
}

# ---------------------------------------------------------------- section 1
S1 = """Back to the documents. `readingMillis` from lesson 1 calls `b.millis()` on every block. That's a call through an interface, so it could go to `Paragraph`, `Heading`, `Quote` or a class nobody has written yet. C2 can only inline it if it knows which one.

The object a method is called on is the **receiver**. At tier 3, C1 records the receiver types it sees at each call site, and C2 reads that **type profile** when it compiles. It's the cook's tally of side dishes, and C2 handles three cases:

- One type seen: C2 inlines that type's method behind a cheap check, "is it a `Paragraph`?". The site is **monomorphic**, one shape. That's the basket of fries by the stove.
- Two types: it inlines both, behind two checks (**bimorphic**). The profile keeps two types per site (`TypeProfileWidth` is 2).
- Three or more: C2 inlines only a type that has at least 90% of the calls (`TypeProfileMajorReceiverPercent`). Otherwise the site is **megamorphic**, and C2 emits a plain virtual call, which looks the method up in the receiver's class at run time and jumps to it. Nothing gets inlined. The cook stops keeping sides ready and reads every order.

`-XX:+PrintInlining` shows the bet. This is the real decision for the `millis()` call in lesson 1's `Hot`, on JDK 21, while only paragraphs had arrived:

```text
@ 27   workbench.performance.l01.Hot$Paragraph::millis (9 bytes)   inline (hot)
 \\-> TypeProfile (1408440/1408440 counts) = workbench/performance/l01/Hot$Paragraph
```

Every one of 1,408,440 calls went to a `Paragraph`, so C2 copied `Paragraph::millis` into the loop.

What happened after the headings and quotes arrived surprised me. The recompiled `readingMillis` still inlined `Paragraph`, with `TypeProfile (1463420/1572265 counts)`: 93% paragraphs. The profile is a running tally since the program started, and 20,000 trips through an article of paragraphs had piled up a lot of marks. On JDK 25, the run's last compile did switch to `failed to inline: virtual call`. The tally remembers the past, and what it says when C2 reads it decides the code.

To watch the number of types on its own, `MegamorphicBench` feeds one call site with 1, 2 or 3 kinds of block, in documents of 1,024 blocks. It's a JMH benchmark (lesson 3 explains JMH), and each case runs in a fresh JVM, so each starts with an empty tally. Two runs on the busy course machine, in nanoseconds per document:

```text
types    run 1    run 2
1          950    1,170
2        2,093    1,547
3        7,913    5,122
```

The error bars on that machine were wider than the scores, so read only the shape: three types cost several times more than one or two. With the calls inlined, C2 can optimize the whole loop. With a virtual call per block, it can't.

Notice what didn't matter. A record is a final class, so `Paragraph` can't have subclasses, yet the log says C2 inlined it from the type profile, not from the modifier. Kotlin classes are final by default, and that changes nothing here either. What changes speed is how many types reach one call site.

So C2 compiles what its tally shows. What does it do about the orders it has never seen?"""

# ---------------------------------------------------------------- section 2
J_DEOPT = """long ms = blocks[i].millis();           // bytecode 16: which types has it seen?
if (folded[i]) total += GLANCE_MILLIS;  // bytecode 27: has this branch ever been taken?
else total += ms;"""
K_DEOPT = """val ms = blocks[i].millis()             // which types has it seen?
if (folded[i]) total += GLANCE_MILLIS   // has this branch ever been taken?
else total += ms"""

S2 = """C2 compiles what the profile showed and nothing else. A branch that was never taken, or a receiver type that never appeared, gets no compiled code. In its place C2 puts an **uncommon trap**, the stub from lesson 1 that hands the running call back to the interpreter if the "impossible" case ever happens.

When a trap fires, the JVM **deoptimizes**: it rebuilds an interpreter frame from the compiled one and carries on in the interpreter. The compiled code is made not entrant. The method goes back to tier 3 for more profiling, now with the new case in its tally, and is compiled again. In the kitchen, the customer who asks for rice sends the cook back to the recipe card, and soon rice is part of the routine. The figure shows the cycle.

`DeoptDemo` trips both common kinds of trap on purpose. It adds up the reading time of a document in three phases. First come paragraphs only. Then each document gets one folded block, such as a hidden spoiler, which costs the reader only a glance. Finally headings and quotes arrive. The loop body:

""" + pair(J_DEOPT, K_DEOPT) + """

The real log on JDK 25, trimmed to the important lines:

```text
phase 2: one folded block per document
... DeoptDemo.readingMillis(...) trap_bci=27 unstable_if reinterpret
224   23       4       ...DeoptDemo::readingMillis (52 bytes)   made not entrant: uncommon trap
phase 3: headings and quotes arrive
... DeoptDemo.readingMillis(...) trap_bci=16 class_check maybe_recompile
255   26       4       ...DeoptDemo::readingMillis (52 bytes)   made not entrant: uncommon trap
```

`unstable_if` means a branch C2 had compiled as never taken: the folded block. `class_check` means a type check failed at a call C2 had inlined for paragraphs only. Each time, a new tier 4 compile followed within a few milliseconds, ids 26 and 37 in this run.

This is normal, and cheap when it happens a few times. HotSpot also caps how often one method can go around the cycle (`PerMethodRecompilationCutoff` is 400 recompiles). Expect a burst of deoptimizations just after a program starts, or when a new kind of input gets its first traffic. A steady stream of them in a service that has been up for hours is worth a look. JFR, the recorder built into the JDK, has a ready-made view for that, `deoptimizations-by-reason`, and lesson 5 uses it.

Here the picture breaks a little. A cook who gets burned by a shortcut might grow careful. C2 doesn't: it recompiles with the new facts and bets again, as boldly as before. That's usually right, because most programs settle into the same few cases.

**C2 compiles only what it has seen. The first unusual input sends the call back to the interpreter.**

Bets and traps are C2 learning about your code. For a few JDK methods, it doesn't need to learn anything."""

# ---------------------------------------------------------------- section 3
J_INTR = """long total = Math.addExact(totalWords, words);   // ArithmeticException on overflow
boolean same = Arrays.equals(textA, textB);
int styles = Long.bitCount(styleBits);"""
K_INTR = """val total = Math.addExact(totalWords, words)     // ArithmeticException on overflow
val same = textA.contentEquals(textB)             // calls java.util.Arrays.equals
val styles = styleBits.countOneBits()             // calls java.lang.Long.bitCount"""

S3 = """Some JDK methods never run as their Java code once they're hot. HotSpot carries hand-written machine code, or hand-written compiler instructions, for them. These are **intrinsics**, and they're the kitchen gadget that does one job perfectly. The recipe card may say "core the apple with a small knife", in twelve careful steps; a cook with an apple corer does it in one push.

In the JDK source, these methods carry `@IntrinsicCandidate`, whose Javadoc says the method "may be (but is not guaranteed to be) intrinsified". `PrintInlining` marks the ones that were:

```text
java.lang.Long::bitCount (61 bytes)   (intrinsic)
java.lang.Math::addExact (32 bytes)   (intrinsic)
java.util.Arrays::equals (43 bytes)   (intrinsic)
```

Those are real lines from `IntrinsicsDemo`, the same on JDK 21 and JDK 25, and the report service has a use for each one. `Long.bitCount` counts the 1 bits in a `long`. The service keeps a document's text styles (bold, italic, underline and so on) as one bit each, so the count says how many are switched on. In Java it's 61 bytes of shifts and masks; on x86, C2 replaces it with a single `POPCNT` instruction. `Math.addExact` adds up the word counts of many documents and throws `ArithmeticException` if the total overflows, instead of quietly wrapping around to a negative number. `Arrays.equals` checks whether two uploaded texts have the same bytes, and ends up in code that compares many bytes per step.

The bytecode size doesn't matter for an intrinsic, because that Java code isn't what runs. Those 61 bytes are still there for a reason, though: they're the instructions for a kitchen without the gadget. The interpreter, or a processor without `POPCNT`, runs the Java version.

The practical rule follows. In hot code, call the JDK method instead of writing the loop yourself. A hand-written loop that compares two texts byte by byte gives up the many-bytes-at-a-time path that `Arrays.equals` gets for free, and it's more code to get wrong.

Kotlin gets the same intrinsics, because its standard library calls these JDK methods. `ByteArray.contentEquals` calls `java.util.Arrays.equals`, and `Long.countOneBits()` calls `java.lang.Long.bitCount`:

""" + pair(J_INTR, K_INTR) + """

That finishes our tour of C2's notebook: it copies small methods, bets on types, loses bets and swaps in gadgets. We've judged every one of those choices with a timing. Which raises a question we've been dodging: how far can a timing taken by hand be trusted?"""

L = {
 "id": "perf-02",
 "title": "Inlining, deoptimization and intrinsics",
 "minutes": 38,
 "goal": "By the end you can read C2's inlining and deoptimization decisions, say why a third type at a call site or a long error path changes speed, and keep a hot method inside the inlining budget.",
 "opening": OPENING,
 "warmup": {
  "q": "A hot loop in the report service calls `block.millis()` on every block of a document. For weeks only `Paragraph` and `Heading` blocks reach that call. Then `Quote` blocks start making up a third of all blocks. What does C2 most likely do with that call?",
  "options": [
   "Nothing changes: the compiled code already handles any `Block`",
   "It throws the compiled code away and recompiles the call as a plain virtual call, with nothing inlined",
   "It inlines all three implementations, because they are small",
   "It stops compiling the method and leaves it in the interpreter for good"
  ],
  "answer": 1,
  "why": "C2 had copied both `millis()` methods into the loop behind type checks, and compiled \"any other type\" as an uncommon trap. The first quote trips the trap, the code is made not entrant, and the recompile sees three types with no 90% favourite. That makes the call site megamorphic: a plain virtual call each time, looked up at run time. It still works, just without inlining. The section on types shows this, and one twist about old tallies."
 },
 "sections": [
  {
   "h": "Inlining: copying a small method into its caller, within a budget",
   "body": S0,
   "aside": ASIDE,
   "try": {
    "title": "See C2 refuse the big check",
    "minutes": 4,
    "steps": [
     "Run `InliningDemo`. It starts a second JVM with `-XX:+UnlockDiagnosticVMOptions -XX:+PrintInlining` and keeps the lines about `summarize` and the two checks.",
     "Find the decisions under the tier 3 compile (C1 says `callee is too large`) and under the tier 4 compile (C2 says `too big`).",
     "Run the Kotlin twin. Compare the size of `requireWordCountInline` in both languages."
    ],
    "code": demo("InliningDemo"),
    "expect": "Both compilers refuse `requireWordCountInline` and inline `requireWordCountSplit`. In Java the sizes are 49 and 21 bytes. In Kotlin the version with the message inline is 66 bytes: `\"...\".format(...)` is an `inline` function, so kotlinc pastes its body (an `Arrays.copyOf` of the arguments and a null check) into the caller. The split version is 21 bytes in both. On JDK 25 each refusal starts with `failed to inline:`."
   },
   "refs": [
    {"title": "bytecodeInfo.cpp: C2's inlining rules (JDK 25)", "url": "https://github.com/openjdk/jdk/blob/jdk-25-ga/src/hotspot/share/opto/bytecodeInfo.cpp", "kind": "read"}
   ]
  },
  {
   "h": "C2 bets on the types it has seen at each call",
   "body": S1,
   "try": {
    "title": "Count the types at a call site",
    "minutes": 5,
    "steps": [
     "Predict the three numbers before you run: nanoseconds per document with 1, 2 and 3 kinds of block.",
     "Run `MegamorphicBench`. Each case runs in a fresh JVM, so each starts with a clean profile. It takes about 10 seconds. On JDK 24 and later, JMH 1.37 makes the JVM print a few `WARNING` lines about `sun.misc.Unsafe`; they're harmless.",
     "Run it with `-Pargs='1 4'`. Does a fourth type cost more than the third? The Kotlin twin runs 1, 3 and 4 types."
    ],
    "code": demo("MegamorphicBench"),
    "expect": "One and two types are close, and three types cost several times more: on the busy course machine, about 1 µs per document for one type and 5 to 8 µs for three. Four types cost about the same as three (7.0 µs in one run): once the site is megamorphic, it's a virtual call either way. Expect wide error bars on any machine with other work running."
   }
  },
  {
   "h": "When a bet loses: uncommon traps and deoptimization",
   "body": S2,
   "figure": {"svg": FIG, "caption": "C2 compiles only what the profile saw. An unseen case hits an uncommon trap, the code is retired, and the method is profiled and compiled again."},
   "try": {
    "title": "Trip a branch trap and a type trap",
    "minutes": 4,
    "steps": [
     "Predict: in which phase will the first `made not entrant` for tier 4 code appear, and with which reason in the deoptimization log?",
     "Run `DeoptDemo`. It starts a second JVM with `-XX:+PrintCompilation -Xlog:deoptimization=debug`.",
     "Match each `trap_bci` to a line of `readingMillis` (bytecode 16 is the `millis()` call, 27 is the `if (folded[i])` test). Then run the Kotlin twin: its bytecode indexes differ, the story doesn't."
    ],
    "code": demo("DeoptDemo"),
    "expect": "Phase 1 compiles `readingMillis` up to tier 4, including an OSR version. Phase 2 prints `unstable_if` at `trap_bci=27`, retires the tier 4 code and recompiles. Phase 3 prints `class_check` at `trap_bci=16`, retires it again and recompiles. On JDK 25 the PrintCompilation lines end in `made not entrant: uncommon trap`; on JDK 21 they just say `made not entrant`. In the Kotlin twin the method is 68 bytes instead of 52, and the traps sit at bytecodes 43 and 32."
   }
  },
  {
   "h": "Intrinsics: JDK methods the JIT swaps for ready-made machine code",
   "body": S3,
   "try": {
    "title": "List the intrinsics in a hot loop",
    "minutes": 3,
    "steps": [
     "Run `IntrinsicsDemo`. It prints the `PrintInlining` lines for the three JDK methods it calls.",
     "Run the Kotlin twin, which uses `contentEquals` and `countOneBits` instead of calling `Arrays` and `Long` directly.",
     "Optional: run the Java demo's second JVM yourself with `-XX:+UnlockDiagnosticVMOptions -XX:+PrintInlining` and search for `intrinsic` to see how many others the JDK uses on its own."
    ],
    "code": demo("IntrinsicsDemo"),
    "expect": "Both programs print the same three lines, each ending in `(intrinsic)`: `Long::bitCount`, `Math::addExact` and `Arrays::equals`. Kotlin's standard library functions disappear entirely: they are `inline`, so the call in the bytecode is already the JDK method."
   }
  }
 ],
 "compare": {
  "title": "The same check, before and after the split",
  "java": {"title": "InliningDemo.java", "src": "// before: 49 bytes, \"too big\" at a call site that isn't hot\n" + INLINE_J + "\n\n// after: 21 bytes, inlined\n" + GUARD_J},
  "kotlin": {"title": "InliningDemo.kt", "src": "// before: 66 bytes, \"too big\" at a call site that isn't hot\n" + INLINE_K + "\n\n// after: 21 bytes, inlined\n" + GUARD_K},
  "note": "After the split, both languages compile `requireWordCount` to the same 21 bytes, and C2 treats them the same. Before the split, the Kotlin version is 66 bytes against Java's 49, because kotlinc pastes the body of the inline `format` extension into the caller: an `Arrays.copyOf` of the arguments and a null check on the result. So the same fix matters a little more in Kotlin. In both languages the cold method still builds exactly the same message, so nobody searching the logs for it will notice the change."
 },
 "worked": {
  "title": "Find out why a hot method isn't inlined, and fix it",
  "steps": [
   {"say": "The report handler is slower than expected in a profile. Start the service with the diagnostic flags and look for the check in the inlining log.", "code": "java -XX:+UnlockDiagnosticVMOptions -XX:+PrintInlining -cp report.jar example.report.Main | grep requireWordCount", "lang": "bash"},
   {"say": "C2's line names the method, its bytecode size and the reason. `too big` means the call site isn't hot and the callee is over 35 bytes. `hot method too big` would mean a hot site and a callee over 325 bytes.", "code": "@ 15   example.report.Guards::requireWordCount (49 bytes)   failed to inline: too big", "lang": "text"},
   {"say": "Look at what the 49 bytes are. `javap -c -p` shows the boxing calls, the argument array and the `String.format` that build the message. All of that is the cold path.", "code": "javap -c -p -cp report.jar example.report.Guards | grep -A 30 'long requireWordCount'", "lang": "bash"},
   {"say": "Move the cold path into its own method and return the exception from it, so the hot method still ends in `throw`. Self-check before reading on: why return the exception instead of throwing it inside the helper? (Answer: with `throw badWordCount(words)`, javac and the next reader can both see that the method ends there. A helper that throws by itself looks like an ordinary call that returns.)", "code": GUARD_J, "lang": "java", "alt_lang": "kotlin", "alt_code": GUARD_K},
   {"say": "Run the same command again. The hot method is 21 bytes and C2 inlines it. Keep the message text identical, because someone's alert or log search may match on it.", "code": "@ 15   example.report.Guards::requireWordCount (21 bytes)   inline (hot)", "lang": "text"}
  ]
 },
 "lab": {
  "title": "Fit two hot checks into the inlining budget",
  "minutes": 12,
  "files": [f"{lab}/main/{P}/DocumentGuards.java"],
  "run": "./gradlew :performance:test --tests 'workbench.performance.l02.*'",
  "steps": [
   "Open `DocumentGuards`, the two checks the report service runs on every document it receives: one for the word count and one for the title. Run the tests. Two pass (the checks behave correctly) and two fail: `requireWordCount` is 49 bytes of bytecode and `requireTitle` is 68. The limit in the test is 35, C2's `MaxInlineSize`.",
   "Check the sizes yourself: after a build, run `javap -c -p -cp performance/build/classes/java/main workbench.performance.l02.DocumentGuards`. The offset of the last instruction plus one is the size.",
   "Move the message building out of `requireWordCount` into a private static method that returns the exception. Keep the exact message.",
   "Do the same for `requireTitle`. The `null` case must still say `got null`.",
   "Run the tests until all four pass. The test reads the compiled class file, so `BytecodeSize.java` in the test folder shows exactly what it measures."
  ],
  "hints": [
   "The shape that fits: `if (bad) throw badWordCount(words); return words;`. Everything about the message goes in `badWordCount`.",
   "`String.format` with two arguments costs a lot of bytecode: an array, two boxing calls and the call itself. In the cold method that doesn't matter.",
   "In `requireTitle`, the `title == null ? \"null\" : ...` choice belongs in the cold method too. Pass the title itself to the helper.",
   "Both fixed methods come out at 21 and 27 bytes in the reference solution."
  ],
  "done_when": "All four tests in `DocumentGuardsTest` pass."
 },
 "drill": {
  "title": "Split a check from memory",
  "minutes": 4,
  "prompt": "Close this page. Write a check `requireLanguage(String code)` that returns `code` when it is exactly 2 characters long, such as `\"en\"`, and otherwise throws `IllegalArgumentException(\"language must be 2 letters, got '\" + code + \"'\")`. Shape it so the hot method stays small. Then write down the two C2 size limits and when each applies.",
  "answer": {"lang": "java", "src": "static String requireLanguage(String code) {\n    if (code == null || code.length() != 2) throw badLanguage(code);   // hot: a check and a call\n    return code;\n}\n\nprivate static IllegalArgumentException badLanguage(String code) {     // cold: everything else\n    return new IllegalArgumentException(\"language must be 2 letters, got '\" + code + \"'\");\n}\n\n// C2 inlines up to 35 bytes of bytecode at a call site that runs on fewer than 25% of the\n// caller's invocations (MaxInlineSize), and up to 325 bytes at a hot one (FreqInlineSize).",
             "alt": {"lang": "kotlin", "src": "fun requireLanguage(code: String?): String {\n    if (code == null || code.length != 2) throw badLanguage(code)      // hot: a check and a call\n    return code\n}\n\nprivate fun badLanguage(code: String?) =                               // cold: everything else\n    IllegalArgumentException(\"language must be 2 letters, got '$code'\")\n\n// C2 inlines up to 35 bytes of bytecode at a call site that runs on fewer than 25% of the\n// caller's invocations (MaxInlineSize), and up to 325 bytes at a hot one (FreqInlineSize)."}}
 },
 "recap": [
  "C2 inlines a callee only within a bytecode budget: 35 bytes at call sites that aren't hot, 325 bytes at hot ones (25% of the caller's calls). Error paths count too, so give them their own method.",
  "At each interface or virtual call, C2 uses the receiver types tier 3 recorded. One or two types get inlined behind type checks. Three or more without a 90% favourite become a plain virtual call. The tally counts everything since the program started.",
  "Whatever the profile never saw becomes an uncommon trap. When one fires, the call goes back to the interpreter, the code is made not entrant, and the method is compiled again with the new case.",
  "`-XX:+UnlockDiagnosticVMOptions -XX:+PrintInlining` and `-Xlog:deoptimization=debug` show these decisions. `inline (hot)` is just C2's success message.",
  "Intrinsics (`@IntrinsicCandidate`) swap JDK methods such as `Math.addExact`, `Arrays.equals` and `Long.bitCount` for ready-made machine code. Kotlin's standard library reaches the same ones.",
  "The limit: these logs explain one method at a time. They can't tell you which of thousands of methods is worth your attention; that takes careful measurement (lesson 3) and a profiler (lessons 5 and 6)."
 ],
 "closing": "We started with a cook who copies short sub-recipes into the main one and keeps fries ready by the stove, until a customer asks for rice. C2 does the same: it inlines small methods within a bytecode budget, bets on the types it has counted, and falls back to the interpreter through an uncommon trap when the unusual order arrives.\n\nNow look at a hot loop in your own code that calls through an interface. Count the classes that can reach that one call. Three or more, with no clear favourite, means a virtual call on every lap.\n\nNext, we'll put all these timings on trial: why does a loop timed with `System.nanoTime()` report work that never ran?",
 "quiz": [
  {"q": "C2's inlining log shows `@ 15   DocumentGuards::requireWordCount (49 bytes)   failed to inline: too big` inside the report handler. Which change is most likely to get it inlined?",
   "options": ["Mark `requireWordCount` as `final`", "Move the message building into a separate method so `requireWordCount` is under 35 bytes", "Raise the heap size with `-Xmx`", "Wrap the call in a lambda"],
   "answer": 1,
   "why": "`too big` means the call site isn't hot, so the 35-byte limit applies, and the cold message code is most of the 49 bytes. A static method is already bound to one implementation, so `final` changes nothing, and the heap has nothing to do with inlining."},
  {"q": "A call site has seen `Paragraph` (50%), `Heading` (30%) and `Quote` (20%). What does C2 compile there?",
   "options": ["Three inlined bodies behind three type checks", "`Paragraph` inlined, the rest as a virtual call", "A plain virtual call, with nothing inlined", "Nothing: the method stays at tier 3"],
   "answer": 2,
   "why": "The profile keeps two types per site, and with more than two C2 needs one type with at least 90% of the calls to inline it. 50% isn't enough, so the site is megamorphic and becomes a virtual call."},
  {"q": "A deoptimization log line reads `trap_bci=27 unstable_if reinterpret`. What happened?",
   "options": ["Bytecode 27 is a branch C2 compiled as never taken; it was taken, so the call went back to the interpreter and the method will be compiled again", "The JVM ran out of code cache at bytecode 27", "A class was loaded twice", "The method threw an exception at bytecode 27"],
   "answer": 0,
   "why": "`unstable_if` is the trap C2 places on a branch the profile never saw taken. When it runs, the JVM deoptimizes the call and the code is made not entrant. `class_check` would be the type-based version."},
  {"q": "The inlining log shows `java.lang.Long::bitCount (61 bytes)   (intrinsic)`. What does that tell you?",
   "options": ["The method was too big to inline", "The method was compiled to 61 bytes of machine code", "The method runs in the interpreter", "C2 replaced the call with ready-made code, so the 61 bytes of Java don't run in that compiled code"],
   "answer": 3,
   "why": "An intrinsic replaces the method body with code HotSpot ships for it, a single POPCNT on x86 for `bitCount`. The size in the line is still the Java bytecode size, which doesn't matter once the intrinsic applies."},
  {"q": "PrintCompilation shows `DeoptDemo::readingMillis (52 bytes)`. Using what lesson 1 said about that number, can C2 inline `readingMillis` into a caller that calls it on only 1 invocation in 10?",
   "options": ["Yes, 52 bytes of machine code is small", "No: 52 bytes of bytecode is over the 35-byte limit for a call site that isn't hot", "Yes, any method under 325 bytes is always inlined", "No, methods with loops are never inlined"],
   "answer": 1,
   "why": "`(52 bytes)` is the bytecode size. A call on 1 invocation in 10 is below the 25% bar, so the 35-byte `MaxInlineSize` applies and 52 is too big. At a hot site the limit would be 325, and it could be inlined.",
   "from": "perf-01"}
 ],
 "flashcards": [
  {"front": "Biggest callee (in bytecode) that C2 inlines at a call site it doesn't consider hot?", "back": "35 bytes (`MaxInlineSize`)."},
  {"front": "When does C2 treat a call site as hot, and what's the size limit there?", "back": "When the call runs on at least 25% of the caller's invocations. Then the limit is 325 bytes (`FreqInlineSize`)."},
  {"front": "How many receiver types does C2 inline at one call site from the profile?", "back": "Up to two. With more, only a type with at least 90% of the calls; otherwise it emits a virtual call (megamorphic)."},
  {"front": "What is an uncommon trap?", "back": "A stub C2 puts where the profile saw nothing, such as an untaken branch or an unseen type. If it runs, the call is deoptimized and the code is made not entrant."},
  {"front": "Does marking a class `final` make calls to it faster in C2?", "back": "Not by itself. C2 inlines from the receiver-type profile. What matters is how many types reach the call site."},
  {"front": "What does `@IntrinsicCandidate` on a JDK method mean?", "back": "HotSpot may replace the method with hand-written machine code or compiler instructions, as it does for `Math.addExact` and `Arrays.equals`."},
  {"front": "Why can a Kotlin function be bigger in bytecode than the same Java code?", "back": "Calls to Kotlin `inline` functions, such as `\"...\".format(x)`, are pasted into the caller by kotlinc, and that bytecode counts against the JIT's inlining budget."}
 ],
 "terms": [
  {"term": "Inlining", "plain": "Pasting a called method's body into the caller so C2 compiles and optimizes them together."},
  {"term": "Call site", "plain": "One specific call instruction in the bytecode. Profiles and inlining decisions are per call site."},
  {"term": "Receiver", "plain": "The object a method is called on: `b` in `b.millis()`."},
  {"term": "Monomorphic, bimorphic, megamorphic", "plain": "One, two, or too many receiver types seen at a call site."},
  {"term": "Uncommon trap", "plain": "A stub in C2 code for a case the profile never saw. Running it deoptimizes the call."},
  {"term": "Deoptimization", "plain": "Turning a compiled frame back into an interpreter frame and retiring the compiled code."},
  {"term": "Intrinsic", "plain": "A JDK method that HotSpot replaces with its own ready-made code."}
 ],
 "explain_back": {
  "prompt": "A colleague asks: \"Why did our report loop get slower when we added a third kind of block, even though the new class is tiny?\" Explain it in your own words.",
  "answer": "The loop calls `millis()` through the `Block` interface. While only paragraphs and headings reached that call, C2 inlined both implementations behind type checks, and could then optimize the loop body as a whole. It compiled any other type as an uncommon trap. When the first quote arrived, the trap fired, the compiled code was thrown away and the method was compiled again. With three types and none above 90%, the call site is megamorphic, so C2 now emits a virtual call for every block and inlines nothing. The size of the new class doesn't matter. What changed is the number of types reaching that one call. One twist: the profile counts everything since start-up, so if paragraphs had piled up 90% of the old counts, C2 might keep inlining them for a while."
 },
 "deeper": {
  "minutes": 10,
  "body": "Inlining is what makes escape analysis work. C2 can only prove that an object never leaves a method if it can see every method the object is passed to. A small result object created in a hot method and passed to a callee that isn't inlined has escaped, so it gets put on the heap. The memory track looks at escape analysis from the allocation side.\n\nFor experiments, `-XX:CompileCommand=dontinline,example.report.Guards::requireWordCount` and `-XX:CompileCommand=inline,...` force a decision for one method, and the inlining log then says it was forced by CompileCommand. Use them to test a theory, not as a production fix.\n\nNot every call through an interface is megamorphic just because many classes pass through it. Take a shared helper such as `static long timed(LongSupplier work)` that three callers use with three different lambdas. Once C2 has inlined `timed` into each caller, it can see the exact lambda class at each spot and doesn't need the shared profile. Megamorphic sites come from types C2 can't see at compile time, such as objects read from an array, a field or a collection.\n\nOther messages you'll meet in the log: `inlining too deep` (more than 15 levels, `MaxInlineLevel`), `already compiled into a big method` (a callee already compiled into more than 2,500 bytes of machine code), `hot method too big` (a hot site, over 325 bytes) and `no static binding` (C1 can't inline a virtual call). JITWatch shows the same information per method if the raw log gets too long."
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
