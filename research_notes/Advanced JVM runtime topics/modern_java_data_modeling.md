# Modern Java Data Modeling (records, sealed types, pattern matching, data-oriented programming, Valhalla) compared with Kotlin. Research notes as of 2026-11-07

How these notes were produced, and how to read them:
- **Scope and relation to earlier notes.** This file builds on `research_notes/JVM concurrency course research/design_patterns.md`. That file already covers these topics, and they are not repeated here: the PaymentState/PaymentEvent State machine with nested switches, the Visitor-vs-switch `Expr` evaluator, Goetz's "Visitor is almost completely unnecessary" quote, the Composite pricing-rule tree, the `notify` component-name clash, and Kotlin `when` guards in a State machine. This file goes deeper on the language semantics, version status and compiler behaviour.
- **Network limits (same as the earlier session).** These hosts were blocked by egress policy (HTTP 403 on CONNECT, or DNS failure in WebFetch): openjdk.org (all JEP pages), docs.oracle.com (JLS 25, Javadoc), inside.java, dev.java, infoq.com, bugs.openjdk.org, cr.openjdk.org, mail.openjdk.org, jdk.java.net, api.github.com, and github.com HTML pages for commits and Adoptium releases.
- **What was used instead (primary sources).**
  - The OpenJDK source tree at tags `jdk-21-ga` … `jdk-27-ga` and `master` (JDK 28 in development), read via `raw.githubusercontent.com`. This includes javac's own feature tables (`Source.java`, `Preview.java`), the `PreviewFeature` enum with JEP numbers, `compiler.properties` (the exact diagnostic texts), and the Javadoc inside `.java` files.
  - A treeless `git clone` of `openjdk/jdk` master history since 2023-06. It gives the "Implement JEP …" commit messages and their dates.
  - Git clones of `openjdk/amber-docs` (Goetz/Bierman design notes, latest commit 2026-08-14) and `openjdk/valhalla-docs`. The latter is the source of openjdk.org/projects/valhalla; latest commit 2026-08-08.
  - A sparse clone of `openjdk/jdk` master: `java.lang`, `java.util`, `java.time`, and the valhalla javac tests.
  - `JetBrains/kotlin-web-site` (the source of kotlinlang.org/docs, commit 2026-11-06) and `Kotlin/KEEP`.
  - The Lombok changelog, and Maven Central metadata.
- **Every Java sample marked [local] was compiled and run in this session.** The toolchain was `javac`/`java` **21.0.12.1** with `--release 21` (no preview flags unless stated). Kotlin samples used **kotlinc-jvm 2.4.21**, the official release zip from GitHub. JUnit labs used **junit-platform-console-standalone 6.1.3**, the same JUnit version as `labs/build.gradle.kts`. No JDK newer than 21 could be downloaded: jdk.java.net and the Adoptium GitHub releases were blocked. Behaviour on JDK 22–28 is therefore documented **from source files at the corresponding GA tag**, not from running it.
- **Evidence tags.**
  - **[src]**: read from a fetched primary source; a link is given.
  - **[local]**: reproduced by compiling or running here.
  - **[search]**: seen only in a web-search result snippet; the page was not fetched. Re-check before quoting.
  - **[bg]**: background knowledge that could not be checked here, because the source was blocked. These items are also listed under Gaps.

---

## Key Question 1: What is the exact status of each feature per JDK version 21 → 27 (and 28-in-development)?

### Takeaway
- Records (16), sealed types (17), `instanceof` patterns (16), pattern `switch` with `case null` and guards (21), and record patterns (21) are all final.
- Unnamed variables/patterns were preview in 21 and final in 22.
- **Primitive types in patterns have been preview in every release from 23 through 27, and are still preview on master (28).**
- **Derived record creation ("withers", JEP 468) has never shipped in any JDK.** It is a Candidate JEP that Brian Goetz described in January 2026 as "on hold".
- **JEP 401 value objects is NOT in JDK 25, 26 or 27.** It was integrated into mainline on 2026-07-31, after JDK 27 forked. That makes it a preview feature of **JDK 28**, scheduled GA 2027-03-23 and still in development.
- The pattern-matching change that matters for 26/27: JDK 27's javac now lists the **missing patterns** in non-exhaustive-switch errors.

### Cited Findings

**Status matrix.** Language features come from javac's `Source.Feature` and `Preview.isPreview`; API preview features come from `PreviewFeature`.

| Feature (JEP) | 21 | 22 | 23 | 24 | 25 (LTS) | 26 | 27 | master = 28 (in dev) |
|---|---|---|---|---|---|---|---|---|
| Records (395) | final (since 16) | final | final | final | final | final | final | final |
| Sealed classes (409) | final (since 17) | final | final | final | final | final | final | final |
| `instanceof` patterns (394) | final (since 16) | … | … | … | … | … | … | final |
| Pattern `switch`, `case null`, guards (441) | **final** | final | final | final | final | final | final | final |
| Record patterns (440) | **final** | final | final | final | final | final | final | final |
| Unnamed variables & patterns (443 → 456) | **preview** (JEP 443) | **final** | final | final | final | final | final | final |
| Primitive types in patterns (455/488/507/530/532) | n/a | n/a | preview (455) | 2nd preview (488) | 3rd preview (507) | 4th preview (530) | 5th preview (532) | still preview |
| Derived record creation / withers (468) | — | — | — | — | — | — | — | **not integrated** |
| Value objects (401) + strict fields (539) | — | — | — | — | — | — | — | **preview, integrated 2026-07-31** |
| Flexible constructor bodies (447/482/492/513) | — | preview | preview | preview | **final** | final | final | final |

The evidence for each cell follows.

- **Final-version levels in javac (master).**
  - `PATTERN_MATCHING_IN_INSTANCEOF(JDK16)`, `RECORDS(JDK16)` and `SEALED_CLASSES(JDK17)`.
  - `CASE_NULL(JDK21)`, `PATTERN_SWITCH(JDK21)`, `UNCONDITIONAL_PATTERN_IN_INSTANCEOF(JDK21)` and `RECORD_PATTERNS(JDK21, Fragments.FeatureDeconstructionPatterns…)`.
  - `UNNAMED_VARIABLES(JDK22)`, `PRIMITIVE_PATTERNS(JDK23)`, `FLEXIBLE_CONSTRUCTORS(JDK25)`, and `VALUE_CLASSES(DEFAULT, Fragments.FeatureValueClasses…)`.
  - Source: [Source.java @ master](https://raw.githubusercontent.com/openjdk/jdk/master/src/jdk.compiler/share/classes/com/sun/tools/javac/code/Source.java) **[src]**
- **Which language features are preview in each release.** The `Preview.isPreview(Feature)` switch, per GA tag **[src]**:
  - jdk-21-ga: `STRING_TEMPLATES`, `UNNAMED_CLASSES`, `UNNAMED_VARIABLES`. [Preview.java @ jdk-21-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-21-ga/src/jdk.compiler/share/classes/com/sun/tools/javac/code/Preview.java)
  - jdk-22-ga: `STRING_TEMPLATES`, `IMPLICIT_CLASSES`, `SUPER_INIT`. **UNNAMED_VARIABLES is gone, so it is final in 22.** [Preview.java @ jdk-22-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-22-ga/src/jdk.compiler/share/classes/com/sun/tools/javac/code/Preview.java)
  - jdk-23-ga: `IMPLICIT_CLASSES`, `FLEXIBLE_CONSTRUCTORS`, `PRIMITIVE_PATTERNS`, `MODULE_IMPORTS`. [Preview.java @ jdk-23-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-23-ga/src/jdk.compiler/share/classes/com/sun/tools/javac/code/Preview.java)
  - jdk-24-ga: the same, plus `JAVA_BASE_TRANSITIVE`. [Preview.java @ jdk-24-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-24-ga/src/jdk.compiler/share/classes/com/sun/tools/javac/code/Preview.java)
  - jdk-25-ga, jdk-26-ga and jdk-27-ga: **only `PRIMITIVE_PATTERNS`**. [25](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/jdk.compiler/share/classes/com/sun/tools/javac/code/Preview.java), [26](https://raw.githubusercontent.com/openjdk/jdk/jdk-26-ga/src/jdk.compiler/share/classes/com/sun/tools/javac/code/Preview.java), [27](https://raw.githubusercontent.com/openjdk/jdk/jdk-27-ga/src/jdk.compiler/share/classes/com/sun/tools/javac/code/Preview.java)
  - master (JDK 28): `PRIMITIVE_PATTERNS` and **`VALUE_CLASSES`**. [Preview.java @ master](https://raw.githubusercontent.com/openjdk/jdk/master/src/jdk.compiler/share/classes/com/sun/tools/javac/code/Preview.java)
- **The JDK 21 `PreviewFeature` enum** lists `@JEP(number=443, title="Unnamed Patterns and Variables")` for `UNNAMED` (preview in 21). [PreviewFeature.java @ jdk-21-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-21-ga/src/java.base/share/classes/jdk/internal/javac/PreviewFeature.java) **[src]**. The final JEP number for 22 is 456 **[bg]**: the JEP page was blocked, and the JDK source does not name it.
- **JDK release dates** (`DEFAULT_VERSION_DATE` in `make/conf/version-numbers.conf`) **[src]**:
  - JDK 21: 2023-09-19
  - JDK 22: 2024-03-19
  - JDK 23: 2024-09-17
  - JDK 24: 2025-03-18
  - JDK 25: 2025-09-16
  - JDK 26: 2026-03-17
  - JDK 27: 2026-09-15
  - master: `DEFAULT_VERSION_FEATURE=28`, `DEFAULT_VERSION_DATE=2027-03-23`
  - Sources: e.g. [jdk-27-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-27-ga/make/conf/version-numbers.conf), [master](https://raw.githubusercontent.com/openjdk/jdk/master/make/conf/version-numbers.conf)
- **Fork points, i.e. which release a mainline commit lands in** (from commit messages in a git clone) **[src]**:
  - "Start of release updates for JDK 26": 2025-06-05. [af87035](https://github.com/openjdk/jdk/commit/af87035b713f8bfe05a007a4d4670cefc6a6aaf2)
  - "… JDK 27": 2025-12-04. [c55287d](https://github.com/openjdk/jdk/commit/c55287d197ef024033f8dfbb5a365cb091bc67fb)
  - "… JDK 28": 2026-06-04. [ca52afa](https://github.com/openjdk/jdk/commit/ca52afa38e47bf1c901d05a817fe76d440bff2bd)
- **Primitive patterns history (implementation commits)** **[src]**:
  - "8303374: Implement JEP 455: Primitive Types in Patterns, instanceof, and switch (Preview)", 2024-01-31, landed in JDK 23. [1733d2e](https://github.com/openjdk/jdk/commit/1733d2ea244756238c302d802511eb1557cd46ac)
  - "8341408: Implement JEP 488 … (Second Preview)", 2024-11-06, landed in JDK 24. [6811a11](https://github.com/openjdk/jdk/commit/6811a11e278118b8b2781f1eaf45d363a3d2db49)
  - "8359145: Implement JEP 530 … (Fourth Preview)", 2025-11-19, landed in JDK 26. [99135d2](https://github.com/openjdk/jdk/commit/99135d2e05bb501fe9f9f0d36abd25894d0f93de)
  - There is no "Implement" commit for JEP 507 (JDK 25) or for the JDK 27 round. That is consistent with re-previews that had no changes.
  - JEP 507 is "Third Preview", targeted to JDK 25, and re-previewed "without change" — [JEP 507](https://openjdk.org/jeps/507), [inside.java 2025-06-17](https://inside.java/2025/06/17/jep507-target-jdk25/) **[search]**
  - JEP 532 is "(5th Preview)", targeted to JDK 27 — [inside.java 2026-05-08](https://inside.java/2026/05/08/jep532-target-jdk27/) **[search]**. That it is still preview at jdk-27-ga is **[src]** (Preview.java above).
- **Withers (JEP 468).**
  - **No commit implementing JEP 468 exists in mainline history** from 2023-06 to 2026-11-07. A `git log --grep` for "JEP 468", "derived record" and "reconstruction" finds only an unrelated JFR commit. **[src]**
  - Goetz, January 2026: "JEP 468 has been 'on hold' for a while, primarily because we were waiting for sufficient confidence that there was a path to extending it to suitable classes before committing to it for records." — [Data-Oriented Programming for Java: Beyond Records (Goetz, Jan 2026)](https://github.com/openjdk/amber-docs/blob/master/site/design-notes/beyond-records.md) **[src]**
  - The JEP page's formal status field reads "Candidate"; the JEP was promoted to Candidate in Feb 2024. An amber-dev thread "Current State of 'withers'" exists from May 2025 — [JEP 468](https://openjdk.org/jeps/468), [jdk-dev 2024-02](https://mail.openjdk.org/pipermail/jdk-dev/2024-February/008744.html), [amber-dev 2025-05](https://mail.openjdk.org/pipermail/amber-dev/2025-May/009295.html) **[search]**
- **Value objects (JEP 401).**
  - Commit "8389219: Implement JEP 401: Value Objects (Preview) / 8389220: Implement JEP 539: Strict Field Initialization in the JVM (Preview)", **2026-07-31**. Co-authors include Dan Smith, Frederic Parain and Roger Riggs. This is 8 weeks after the JDK 28 fork-start of 2026-06-04, so it is in JDK 28, not 27. [cc278db](https://github.com/openjdk/jdk/commit/cc278dbb8a1ca0754d5842708b9029441055d361) **[src]**
  - `PreviewFeature` on master has `@JEP(number=401, title="Value Classes and Objects", status = "Preview") VALUE_OBJECTS` and `@JEP(number = 539, title = "Strict Field Initialization in the JVM", status = "Preview") STRICT_FIELDS`. jdk-27-ga has neither. [PreviewFeature @ master](https://raw.githubusercontent.com/openjdk/jdk/master/src/java.base/share/classes/jdk/internal/javac/PreviewFeature.java), [@ jdk-27-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-27-ga/src/java.base/share/classes/jdk/internal/javac/PreviewFeature.java) **[src]**
  - Note the naming drift: the enum title is still "Value Classes and Objects", while the commit and the Valhalla page say "Value Objects (Preview)".
  - The Valhalla project page (Aug 2026): "JEP 401: Value Objects (Preview) and JEP 539 … are now integrated and will be included in JDK 28! Try out value objects today with an early-access JDK 28 build." — [valhalla-docs _index.md](https://github.com/openjdk/valhalla-docs/blob/main/site/_index.md) **[src]**
  - Secondary coverage (InfoQ Aug 2026, The Register) reports the same. One report says Goetz called exit from preview by JDK 29 "optimistic" — [InfoQ](https://infoq.com/news/2026/08/jep401-value-objects-preview) **[search]**, unverified quote.
- **Pattern-matching changes in 26/27/28 (javac).** These are all bug-fix or diagnostic changes; there are no new pattern forms. **[src]**
  - **JDK 26** fixes:
    - "8366968: Exhaustive switch expression rejected by for not covering all possible values" (2025-10-30). [87a4772](https://github.com/openjdk/jdk/commit/87a47721981bb84b1e22b5b2d8d24bc60c8b7223)
    - "8364991: Incorrect not-exhaustive error" (2025-11-18). [2e68b79](https://github.com/openjdk/jdk/commit/2e68b79a3973c8a3dde6b47f19b19c0c7faacc51)
  - **JDK 27**:
    - "8367530: The exhaustiveness errors could be improved" (2026-02-04) adds `compiler.err.not.exhaustive.details`: "the switch expression does not cover all possible input values\n missing patterns:", and lists the missing patterns in the forms `{0} _` and `{0}({1})`. [84e8787](https://github.com/openjdk/jdk/commit/84e8787d1fdfe2d92f8b2c9b959651d8d63be91b), [compiler.properties @ jdk-27-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-27-ga/src/jdk.compiler/share/classes/com/sun/tools/javac/resources/compiler.properties). The text is absent from [jdk-26-ga's compiler.properties](https://raw.githubusercontent.com/openjdk/jdk/jdk-26-ga/src/jdk.compiler/share/classes/com/sun/tools/javac/resources/compiler.properties).
    - "8383414: Exhaustiveness rejects a type pattern that covers all permitted subtypes" (2026-05-04). [5ccf99b](https://github.com/openjdk/jdk/commit/5ccf99b8e921269d7e8deedbd9b8bdd131d91f3a)
  - **JDK 28 (in development)**:
    - "8385563: javac non-exhaustive switch diagnostic should avoid mentioning inaccessible types" (2026-09-08). [83c9689](https://github.com/openjdk/jdk/commit/83c9689bd612e82904db959dcf8c9cc08e45e210)
    - "8385488: Compiler allows "case _ when" in switches, but JLS doesn't" (2026-10-08). By implication javac 22–27 accepted `case _ when …` (inferred from the commit title, not run), and 28 will reject it. [ee4d42c](https://github.com/openjdk/jdk/commit/ee4d42c8fae5cd57e484d19d06e26c013f04486c)
    - "8387668: javac should warn on use of value classes" (2026-08-27). [3c0d1f5](https://github.com/openjdk/jdk/commit/3c0d1f5294b2d430c1d9f0f6aedd2f68149f9c19)
- **On the horizon (design stage, not JEPs in any release).**
  - Goetz (Jan 2026) announces the "next 'data oriented programming' feature arc: _carrier classes_ (and interfaces)", and mentions "the upcoming _pattern assignment statement_ feature" (an amber-spec-experts thread, Jan 2026). [beyond-records.md](https://github.com/openjdk/amber-docs/blob/master/site/design-notes/beyond-records.md) **[src]**
  - Null-restricted types are **Draft** JEPs only. The Valhalla page's JEP table lists:
    - "Null-Restricted Value Class Types (Preview)" (draft 8316779): Draft
    - "JEP 402: Enhanced Primitive Boxing (Preview)": Draft
    - The legacy page lists "Null-Restricted and Nullable Types (Preview)" (draft 8303099) as "proposed general-purpose typing features for managing nulls in Java"
    - Sources: [_index.md](https://github.com/openjdk/valhalla-docs/blob/main/site/_index.md), [legacy.md](https://github.com/openjdk/valhalla-docs/blob/main/site/legacy.md) **[src]**
  - javac on master has value-class diagnostics but **no null-restriction (`!`/`?`) syntax or diagnostics**: a grep of master `compiler.properties` for null-restricted/nullness finds nothing. **[src]**

### Inferences
- For a course pinned to `--release 21`, everything in the records / sealed / pattern-switch / record-pattern core is final. **Two things are not available on 21:**
  - `_` needs `--enable-preview` on 21; it is final from 22.
  - Primitive patterns are preview everywhere through 27.
- For JDK 25 LTS users, `_` and flexible constructor bodies (statements before `this(...)`/`super(...)`) are final. That matters for record non-canonical constructors.
- Lessons should say "JDK 27 improves the error message" rather than "JDK 27 changes exhaustiveness". The rules themselves only got bug fixes.
- Saying "Valhalla is in JDK 25" (or 26, or 27) is wrong. The accurate phrasing: "JEP 401 is a preview feature integrated into the JDK 28 mainline, scheduled for March 2027; early-access builds exist."

### Gaps
- None of the JEP pages could be fetched. The following are therefore [bg] or [search], not [src]:
  - JEP numbers for the final versions: 456 (unnamed, JDK 22), and 447/482/492/513 (flexible constructor bodies).
  - JEP 507 and JEP 532 targeting.
  - JEP 468's formal "Candidate" field.
  - JEP 401's "Targeted to 28" field.
- Whether JDK 27's JEP 532 had any spec change versus JEP 530 is unverified. A HappyCoders snippet said "no fundamental changes since Java 26" **[search]**.
- JDK 28 is in development. JEP 401 could in principle be dropped before GA (2027-03-23); this is unlikely, but it is a scheduled-not-shipped fact.
- JLS 25 sections could not be fetched (docs.oracle.com blocked). Section numbers below come from `@jls` tags in the Javadoc: 8.10 Record Classes, 14.11.3, 14.30.2, 15.28.2.

---

## Key Question 2: Records in depth: what are the exact semantics, what does javac say, and what does the bytecode look like? (verified on JDK 21)

### Takeaway
- A record is a **shallowly immutable, transparent, nominal carrier** of a fixed component list.
- javac generates the following, unless you declare them yourself:
  - a private final field per component
  - a public accessor per component
  - a canonical constructor
  - `equals`/`hashCode`/`toString`, each implemented by an `invokedynamic` to `java.lang.runtime.ObjectMethods.bootstrap`, which is passed **direct field getters**
- The compact constructor is the single choke point for validation and normalisation. That choke point covers every path: `new`, static factories, deserialization, and (if it ships) `with`.
- Records are **identity objects** in JDK 21–27. Their immutability is only one level deep.

### Cited Findings
- **Official definition.**
  - "A _record class_ is a shallowly immutable, transparent carrier for a fixed set of values, called the _record components_."
  - Mandated members: "a _canonical constructor_, which must provide at least as much access as the record class…; a private final field corresponding to each component…; a public accessor method corresponding to each component".
  - Reasons to write an explicit canonical constructor: "to validate constructor arguments, perform defensive copies on mutable components, or normalize groups of components (such as reducing a rational number to lowest terms.)"
  - Source: [Record.java @ jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/lang/Record.java) **[src]**
- **The copy invariant.** "if a record R's components are `c1, c2, ... cn`, then if a record instance is copied as follows: `R copy = new R(r.c1(), r.c2(), ..., r.cn());` then it must be the case that `r.equals(copy)`." — [Record.java](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/lang/Record.java) **[src]**
- **equals semantics.** "true if and only if the argument is an instance of the same record class … and each component … is equal". The rules per component:
  - Reference components use `Objects.equals(this.c, r.c)`.
  - Primitive components use "`PW.compare(this.c, r.c)` would return 0", where PW is the wrapper class.
  - The precise algorithm "is unspecified and is subject to change".
  - Source: [Record.java](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/lang/Record.java) **[src]**
- **Consequences of `Double.compare`, verified [local]:**
  - `new D(Double.NaN).equals(new D(Double.NaN))` is `true`, while `Double.NaN == Double.NaN` is `false`.
  - `new D(0.0).equals(new D(-0.0))` is `false`, while `0.0 == -0.0` is `true`.
  - An `int[]` component compares by reference: `new Arr(new int[]{1}).equals(new Arr(new int[]{1}))` is `false`, and `toString` prints `Arr[values=[I@<hash>]`.
- **hashCode and toString are deliberately underspecified.**
  - hashCode: "The precise algorithm … is unspecified and is subject to change… a component of primitive type may contribute its bits to the hash code differently than the `hashCode` of its primitive wrapper class."
  - toString: "The precise format … is subject to change, so the present syntax should not be parsed by applications to recover record component values."
  - Source: [Record.java](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/lang/Record.java) **[src]**
- **ObjectMethods.**
  - "Bootstrap methods for state-driven implementations of core methods, including `equals`, `hashCode`, and `toString`… used, for example, by Java compiler implementations to implement the bodies of `Object` methods for record classes."
  - `bootstrap(Lookup, String methodName, TypeDescriptor, Class<?> recordClass, String names, MethodHandle... getters)`: `names` is "the list of component names, joined into a string separated by ';'"; `methodName` "must be one of equals, hashCode, or toString".
  - Since 16.
  - Source: [ObjectMethods.java @ jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/lang/runtime/ObjectMethods.java) **[src]**
- **javap of `public record Point(int x, int y) {}`** (javac 21, `--release 21`) **[local]**:
  ```
  public final class Point extends java.lang.Record {
    private final int x;
    private final int y;
    public Point(int, int);
    public final java.lang.String toString();
    public final int hashCode();
    public final boolean equals(java.lang.Object);
    public int x();
    public int y();
  }
  public final java.lang.String toString();
    Code:
       0: aload_0
       1: invokedynamic #16,  0   // InvokeDynamic #0:toString:(LPoint;)Ljava/lang/String;
       6: areturn
  public final boolean equals(java.lang.Object);
    Code:
       0: aload_0
       1: aload_1
       2: invokedynamic #24,  0   // InvokeDynamic #0:equals:(LPoint;Ljava/lang/Object;)Z
       7: ireturn
  Record:
    int x;
      descriptor: I
    int y;
      descriptor: I
  BootstrapMethods:
    0: #43 REF_invokeStatic java/lang/runtime/ObjectMethods.bootstrap:(Ljava/lang/invoke/MethodHandles$Lookup;Ljava/lang/String;Ljava/lang/invoke/TypeDescriptor;Ljava/lang/Class;Ljava/lang/String;[Ljava/lang/invoke/MethodHandle;)Ljava/lang/Object;
      Method arguments:
        #8 Point
        #39 x;y
        #41 REF_getField Point.x:I
        #42 REF_getField Point.y:I
  ```
  - Class flags: `ACC_PUBLIC, ACC_FINAL, ACC_SUPER`; `super_class: java/lang/Record`; class-file major version 65.
  - The three Object methods share **one** bootstrap entry.
  - The "getters" javac passes are `REF_getField` handles on the private fields, not the accessor methods.
- **Accessor override vs. generated methods (a PII/masking trap)** **[local]**. Code: `record Masked(String card) { public String card() { return "****" + card.substring(card.length()-4); } }`. Output:
  ```
  accessor: ****1111
  toString: Masked[card=4111111111111111]
  copy-invariant holds? false
  record pattern binds via accessor: ****1111
  ```
  - Because the generated `toString`/`equals` read the field (see `REF_getField` above), overriding the accessor **does not mask `toString`**.
  - It also breaks the `Record.equals` copy invariant.
  - Record patterns, however, go through the accessor.
- **Compact constructor: validation and normalisation** **[local]**. Code:
  ```java
  record Money(long minor, String currency) {
      Money {                                   // compact canonical constructor
          Objects.requireNonNull(currency, "currency");
          if (minor < 0) throw new IllegalArgumentException("negative amount: " + minor);
          currency = currency.toUpperCase();    // reassign the PARAMETER; fields are assigned after the body
      }
      Money(long minor) { this(minor, "EUR"); } // non-canonical: must delegate
      static Money ofMajor(long major, String ccy) { return new Money(Math.multiplyExact(major, 100), ccy); }
  }
  ```
  Output:
  ```
  Money[minor=1250, currency=EUR]   (from new Money(1250, "eur"))
  Money[minor=5, currency=EUR]      (from new Money(5))
  Money[minor=300, currency=USD]    (from Money.ofMajor(3, "usd"))
  IAE: negative amount: -1
  NPE: currency
  ```
- **javac 21 diagnostics for record rules (exact text)** **[local]**:
  - Assigning a field in a compact constructor:
    ```
    Bad.java:4: error: cannot assign a value to final variable lo
            this.lo = lo;
                ^
    ```
  - A non-canonical constructor that does not delegate:
    ```
    Bad2.java:2: error: constructor is not canonical, so its first statement must invoke another constructor of class Bad2
        Bad2(int x, int y) { }
        ^
    ```
  - An instance field:
    ```
    Bad3.java:2: error: field declaration must be static
        private int cache;
                    ^
      (consider replacing field with record component)
    ```
  - `extends`: a *parse* error. `record Bad4(int x) extends Base { }` gives `error: '{' expected`.
  - An accessor with the wrong type:
    ```
    Bad5.java:2: error: invalid accessor method in record Bad5
        public long x() { return x; }
                    ^
      (return type of accessor method x() must match the type of record component x)
    ```
  - Already in the earlier notes: a component named `notify` gives "illegal record component name".
- **Flexible constructor bodies are final in JDK 25** (`FLEXIBLE_CONSTRUCTORS(JDK25)`). On 25+, a non-canonical record constructor may run statements (e.g. argument checks) *before* `this(...)`. On 21, the first statement must be `this(...)`, as the Bad2 error shows. — [Source.java @ master](https://raw.githubusercontent.com/openjdk/jdk/master/src/jdk.compiler/share/classes/com/sun/tools/javac/code/Source.java) **[src]**. Not run locally (no JDK 25 binary).
- **Shallow immutability and defensive copies** **[local]**:
  - `Cart(String id, List<String> items)` built from a caller's `ArrayList`. Afterwards, `src.add("pen")` changes the record: `Cart[id=c1, items=[book, pen]]`, and `hashCode` changes.
  - A Cart used as a `HashSet` key whose list is then mutated gives `set.contains(k) == false` (a lost key).
  - Fix: `SafeCart { items = List.copyOf(items); }`. The record is then isolated from the caller's list. `items().add(..)` throws `UnsupportedOperationException`, and `List.copyOf` rejects `null` elements with an NPE. That is a feature for domain data, but a surprise for JSON-mapped lists with nulls.
  - Array components need `clone()` in the constructor **and** in the accessor, plus hand-written `equals`/`hashCode`/`toString` (e.g. `Arrays.equals`). Shown working in `ArrSafe`. Prefer `List<Integer>` or an immutable wrapper.
- **Serialization uses the canonical constructor.**
  - "During deserialization the record's canonical constructor is invoked to construct the record object. Certain serialization-related methods, such as readObject and writeObject, are ignored for serializable records." The spec reference is Serialization Spec §1.13. — [Record.java](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/lang/Record.java) **[src]**
  - Verified with `record Range(int lo, int hi) implements Serializable` whose compact constructor checks `lo <= hi` **[local]**:
    - A round trip invokes the canonical constructor exactly once during `readObject`.
    - Swapping the two int values in the byte stream (offset 36) makes deserialization fail with: `java.io.InvalidObjectException: lo > hi: 5 > 1 / cause: java.lang.IllegalArgumentException: lo > hi: 5 > 1`.
  - So the invariant that ordinary classes need `readObject` to re-check is enforced for free.
  - Goetz's rationale: records are "transparent" carriers that can be mapped to and from external forms through the constructor — [records-and-sealed-classes.md](https://github.com/openjdk/amber-docs/blob/master/site/design-notes/records-and-sealed-classes.md) ("Records and externalization") **[src]**
- **Reflection.** `Cart.class.isRecord()` is `true`, and `getRecordComponents()` gives `[String id, List items]` **[local]**. Record.java points to `Class#isRecord()` and `Class#getRecordComponents()` **[src]**.
- **Identity.** On JDK 21, `new D(1.0) == new D(1.0)` is `false`, and `synchronized (new D(1.0)) {…}` compiles and runs **[local]**. Records are identity classes; see KQ6 for `value record`.
- **Withers today (JDK 21–27) are hand-written.**
  - Goetz: "if our `Point` record wants to expose a way to 'set' the `x` and `y` components, it has to write `withX` and `withY` methods… while a class might have O(n) getters, it could conceivably have O(2^n) withers… Let's nip this one in the bud before it becomes a 'pattern' (or worse, a 'best practice'.)" — [reconstruction-records-and-classes.md (Goetz, Aug 2020, "early stage draft")](https://github.com/openjdk/amber-docs/blob/master/eg-drafts/reconstruction-records-and-classes.md) **[src]**
  - The proposed JEP 468 syntax is `Complex cConjugate = c with { im = -im; };`. The block "can contain any Java statements"; the expression destructures through the canonical deconstruction pattern, runs the block over mutable "component variables", then calls the canonical constructor, so "if the new state is not valid, the reconstruction will fail." — [beyond-records.md (Jan 2026)](https://github.com/openjdk/amber-docs/blob/master/site/design-notes/beyond-records.md) **[src]**. This is **not available in any JDK**.
- **Lombok (for the "records vs Lombok vs data class" slide).**
  - Lombok **1.18.48 (2026-09-01)** is the latest release: "PLATFORM: JDK27 support added". 1.18.46 (2026-04-22) added JDK 26 support; 1.18.40 (2025-09-04) added JDK 25 support. — [Lombok changelog](https://raw.githubusercontent.com/projectlombok/lombok/master/doc/changelog.markdown), [Maven metadata](https://repo1.maven.org/maven2/org/projectlombok/lombok/maven-metadata.xml) **[src]**
  - Since 1.18.20 (2021-04-02): "All lombok features updated to act in a sane fashion with JDK16's _record_ feature. In particular, you can annotate record components with `@NonNull` to have lombok add null checks to your compact constructor". The 1.18.48 notes mention "`@With` methods and `@Builder.build()`". **[src]**
  - That Lombok's `@With`/`@Builder` work on records is **[bg]**; the docs site was not fetched.
- **Goetz on what records are for.** Records model "the state, the whole state" and are "transparent; they give up their data freely". The "Algebraic Annie / Tuple Tommy" framing: "a data class is just an algebraic product type… just a nominal tuple". — [records-and-sealed-classes.md](https://github.com/openjdk/amber-docs/blob/master/site/design-notes/records-and-sealed-classes.md) **[src]**
- **Beyond records (Jan 2026).** "records have strict constraints, and not all data holder classes fit… Even a small deviation from the record ideal means one has to go back to a blank slate… the user experience is like falling off a cliff." Proposed *carrier classes*, e.g. `class Point(int x, int y) { … }`, would get the canonical constructor, deconstruction pattern, accessors and derived Object methods without the record's representation constraints. This is a **design note, not a JEP**. — [beyond-records.md](https://github.com/openjdk/amber-docs/blob/master/site/design-notes/beyond-records.md) **[src]**

### Inferences
- **Teach the compact constructor as "the only door".**
  - Validation there covers `new`, every factory, every non-canonical constructor (they must delegate), deserialization, and future `with` expressions.
  - Kotlin's `init {}` plays the same role: `copy()` also runs it [local, KQ7].
- **The accessor-override demo is the best way to make "transparent" concrete.** You cannot hide state in a record. If you need masking, use a different `toString` or a non-record class.
- **Use `List.copyOf`/`Set.copyOf`/`Map.copyOf` in the compact constructor by default.** Teach the null-rejection consequence explicitly.

### Gaps
- The Java Object Serialization Specification §1.13 itself was not fetched (docs.oracle.com blocked). Its exact list of ignored methods (writeObject, readObject, readObjectNoData, serialPersistentFields) and honoured methods (writeReplace/readResolve) is **[bg]**.
- Lombok's `@With`-on-records behaviour was not verified by compiling with Lombok.

---

## Key Question 3: Sealed classes and interfaces: what are the rules, and what does javac say?

### Takeaway
- `sealed` restricts the **direct** subtypes to a known list.
- Each permitted subtype must itself be `final` (records are implicitly final), `sealed`, or `non-sealed`. `non-sealed` deliberately re-opens one branch.
- Permitted subtypes must be in the **same module**, or in the **same package** when in the unnamed module.
- `permits` may be omitted when all subtypes are in the same compilation unit.
- Sealing gives the compiler the information to check exhaustiveness. The JVM also enforces it through the `PermittedSubclasses` attribute and reflection.

### Cited Findings
- **A class not listed in `permits`** **[local]**:
  ```
  S.java:4: error: class is not allowed to extend sealed class: Vehicle (as it is not listed in its 'permits' clause)
  final class Bike implements Vehicle {}
        ^
  ```
- **A permitted subclass without a modifier** **[local]**:
  ```
  S.java:3: error: sealed, non-sealed or final modifiers expected
  class Cat implements Animal {}
  ^
  ```
- **Unnamed module, permitted subclass in another package** **[local]**:
  ```
  a/I.java:2: error: class I in unnamed module cannot extend a sealed class in a different package
  public sealed interface I permits b.Impl {}
                                     ^
  ```
  - The message key is `compiler.err.class.in.unnamed.module.cant.extend.sealed.in.diff.package` — [compiler.properties @ jdk-27-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-27-ga/src/jdk.compiler/share/classes/com/sun/tools/javac/resources/compiler.properties) **[src]**
  - The same two files plus `module m { exports a; }` compile cleanly (exit 0) **[local]**. So the rule is same *module* for named modules, and same *package* otherwise.
- **Inferred `permits`, `non-sealed`, and reflection** **[local]**:
  - `sealed interface Event {}` with `Created`, `Deleted` records and `non-sealed interface Custom extends Event` in one file compiles.
  - `Event.class.getPermittedSubclasses()` gives `[class Created, class Deleted, interface Custom]`.
  - `Event.class.isSealed()` is `true`, and `Custom.class.isSealed()` is `false`.
  - A switch with `case Custom c` covers every (unknown) `Custom` implementation. `handle(new Plugin("x"))` gives `custom Plugin[name=x]`.
- **Sealed abstract class + final subclasses works as a sum type**: `eval(new Neg(new Num(4)))` gives `-4` with an exhaustive switch and no default **[local]**.
- **A concrete (non-abstract) sealed class is not covered by its subtypes**, because `new Fruit()` is itself a possible value **[local]**:
  ```
  Conc.java:5: error: the switch expression does not cover all possible input values
      static String name(Fruit f) { return switch (f) { case Apple a -> "apple"; case Orange o -> "orange"; }; }
                                           ^
  ```
  - The Amber exhaustiveness guide gives the same rule: a "match-all `case`" (`case Fruit other`) is needed "when the `sealed` type is a concrete class and therefore can be instantiated" — [exhaustiveness-guide.md (Bimpoudis, Buckley, Goetz, 2026-08-11)](https://github.com/openjdk/amber-docs/blob/master/site/guides/exhaustiveness-guide.md) **[src]**
- **Two reasons to seal** (Amber guide, 2026):
  - "To signal to clients that this type models a closed-end domain".
  - "To control all the _implementations_ of the type, but not model a specific closed-end domain".
  - The guide adds: "It is helpful when authors of `sealed` types explicitly document the reason for sealing, and how they expect the type to evolve." Its example of inaccessible permitted subtypes is the JDK Class-File API's `Attribute` interface. **[src]**
- **Kotlin rule for comparison.** "Direct subclasses of sealed classes and interfaces must be declared in the same package", and in the same module. In multiplatform `expect` declarations you "still need an `else` branch". — [Kotlin sealed classes (doc source)](https://github.com/JetBrains/kotlin-web-site/blob/master/docs/topics/sealed-classes.md) **[src]**

### Inferences
- "Sealed means final" is wrong in both directions:
  - A sealed type has subtypes, by definition.
  - A `non-sealed` subtype can be extended by anyone.
  - A concrete sealed class can be instantiated itself.
- Kotlin and Java agree on same-module and same-package. Java is stricter only in the unnamed module (same package). Kotlin has no `non-sealed`; its equivalent is an `open` subclass of a sealed class.

### Gaps
- The JLS 8.1.1.2 / 8.1.6 / 9.1.1.4 texts were not fetched (blocked).
- The JVM `PermittedSubclasses` attribute check at class-load time was not demonstrated (it would need hand-crafted class files).

---

## Key Question 4: Pattern matching: instanceof, switch, record patterns, guards, null, dominance, exhaustiveness, unnamed and primitive patterns (javac 21 behaviour + newer)

### Takeaway
A pattern `switch` is **not** sugar for an `instanceof` chain:
- javac checks **exhaustiveness**, which `if` chains never get.
- It checks **dominance**: unreachable labels are compile errors.
- It defines **null** behaviour.
- It compiles to an `invokedynamic` `SwitchBootstraps.typeSwitch` with a synthetic `MatchException` arm. That arm handles the "remainder": `null` inside nested patterns, and subtypes added under separate compilation.

Record patterns nest, infer generic type arguments, and work in `instanceof`. Guards (`when`) do not count toward exhaustiveness.

### Cited Findings
- **Non-exhaustive switch over a sealed interface (javac 21, exact text)** **[local]**. Code: `sealed interface Shape permits Circle, Square, Rect`, with cases for only `Circle` and `Square`:
  ```
  Area.java:7: error: the switch expression does not cover all possible input values
          return switch (s) {
                 ^
  Area.java:13: error: the switch statement does not cover all possible input values
          switch (s) {
          ^
  2 errors
  ```
  - A switch *statement* that uses patterns must also be exhaustive (second error).
  - The `if/else instanceof` version that forgets `Rect` compiled with **no diagnostic**.
- **JDK 27+ wording** (from javac's own diagnostic examples and tests; not run here) **[src]**:
  - The message key `compiler.err.not.exhaustive.details` is "the switch expression does not cover all possible input values\n missing patterns:". The missing cases are rendered by `compiler.misc.binding.pattern` (`{0} _`), `compiler.misc.record.pattern` (`{0}({1})`) and `compiler.misc.enum.constant.pattern` (`{0}.{1}`). — [compiler.properties @ jdk-27-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-27-ga/src/jdk.compiler/share/classes/com/sun/tools/javac/resources/compiler.properties)
  - Test expectations in [ExhaustivenessConvenientErrors.java](https://github.com/openjdk/jdk/blob/84e8787d1fdfe2d92f8b2c9b959651d8d63be91b/test/langtools/tools/javac/patterns/ExhaustivenessConvenientErrors.java):
    - `case R(A a) -> 0;` over `record R(S s)` with `sealed S permits A, B` reports missing pattern `lib.R(lib.B _)`.
    - `case R(A a, B b)`, `case R(B b, A a)` over `R(S s1, S s2)` reports `lib.R(lib.A _,lib.A _)` and `lib.R(lib.B _,lib.B _)`.
- **The same nested gap on 21** (no list of missing cases) **[local]**. Code: `record Pair(Light a, Light b)` with `sealed Light permits Red, Green`, and cases `Pair(Red a, Red b)` and `Pair(Green a, Light b)` (missing `Pair(Red, Green)`):
  ```
  Pairs.java:7: error: the switch expression does not cover all possible input values
          return switch (p) {
                 ^
  ```
- **Dominance errors (exact text)** **[local]**:
  ```
  Dom.java:5: error: this case label is dominated by a preceding case label
              case String s -> "s";            // after case CharSequence cs
                   ^
  Dom.java:12: error: this case label is dominated by a preceding case label
              case Integer x when x > 0 -> "pos";   // after unguarded case Integer x
                   ^
  DomC.java:12: error: this case label is dominated by a preceding case label
              case 1 -> "one";                 // after unguarded case Integer x
                   ^
  DomC.java:18: error: this case label is dominated by a preceding case label
              case String s: return "s";       // after default:
                   ^
  ```
  Allowed (no error) on javac 21:
  - `case Integer x when x > 0 -> …; case Integer x -> …;`: a guarded label does not dominate the unguarded one.
  - `case Integer x when x > 0 -> …; case 1 -> …; default -> …`: a guarded pattern before a constant.
  - Other related messages in `compiler.properties`: "duplicate unconditional pattern"; "switch has both an unconditional pattern and a default label"; "this case label has a guard that is a constant expression with value 'false'"; "guards are only allowed for case with a pattern"; "illegal fall-through to a pattern". **[src]** — [compiler.properties @ jdk-27-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-27-ga/src/jdk.compiler/share/classes/com/sun/tools/javac/resources/compiler.properties)
- **Multiple patterns in one label with bindings are rejected on 21** **[local]**:
  ```
  Lifecycle.java:12: error: illegal fall-through from a pattern
                  case Capture _x, Refund _y -> throw illegal(p, c);
                                   ^
  ```
  On 22+, unnamed patterns allow `case Capture _, Refund _ ->`. The 2026 Amber guide uses exactly that form: `case Fruit _, Dessert _ -> "other food";` — [exhaustiveness-guide.md](https://github.com/openjdk/amber-docs/blob/master/site/guides/exhaustiveness-guide.md) **[src]**
- **Unnamed `_` on JDK 21 is preview** **[local]**:
  ```
  U.java:2: error: unnamed variables are a preview feature and are disabled by default.
  class U { static int x(Object o) { return o instanceof P(int x, _) ? x : -1; } }
                                                                   ^
    (use --enable-preview to enable unnamed variables)
  ```
  With `--release 21 --enable-preview` it compiles, with the note "U.java uses preview features of Java SE 21." It is final in 22 (KQ1).
- **Primitive patterns / primitive selectors on JDK 21** (preview from 23) **[local]**:
  ```
  Prim.java:1: error: selector type long is not allowed            // switch (longValue) { case 1L -> ... }
  Prim2.java:1: error: unexpected type  required: reference  found: int      // i instanceof byte b
  Prim2.java:1: error: unexpected type  required: class or array  found: byte
  Prim3.java:1: error: unexpected type  required: class or array  found: int // case int i -> ...
  ```
  - The feature name in javac is "primitive patterns" (`compiler.misc.feature.primitive.patterns`). On 23–27 it needs `--enable-preview`. **[src]**
  - The 2026 Amber guide restates the current final rule: "For primitive types other than `boolean`, `default` is the only label that covers all the unlisted values". **[src]**
- **Null handling** **[local]**:
  - `switch (s) { case "a" -> …; default -> … }` with `s == null` throws `NullPointerException`. This is the old switch behaviour, kept.
  - `case null -> "null!"` handles it.
  - `case String str -> …; case null, default -> …` gives `null or other` for both `null` and `42`.
  - `null instanceof Object` is `false`.
  - Amber guide: "a `default` is not a true catch-all: it does not handle a `null` selector… write an explicit `case null` or, preferably, use `Objects.requireNonNull` to reject `null` before the `switch`." **[src]**
- **Nested type patterns match null components; record patterns do not** **[local]**:
  - With cases `Line(Point(var x1, var y1), Point(int x2, int y2)) when …`, `Line(Point(…), Point(…)) when …`, then `case Line(Point from, Point to)`:
  - `describe(new Line(null, new Point(1,1)))` returns `diagonal null->Point[x=1, y=1]`. The record patterns skipped the null component, and the type pattern `Point from` (unconditional for the component type) matched `null`.
- **The MatchException remainder.**
  - Javadoc: `MatchException` "may be thrown when an exhaustive pattern matching language construct (such as a `switch` expression) encounters a value that does not match any of the specified patterns at run time". The listed cases:
    - "Separate compilation anomalies… if a sealed interface has a different set of permitted subtypes at run time than it had at compile time, or if an enum class has a different set of enum constants".
    - `null` with nested patterns: "`R(A a)` and `R(B b)` together are considered to be exhaustive for the type `R`, but neither… will match against the result of `new R(null)`".
    - Accessor exceptions during record-pattern matching are wrapped, with "the original exception… set as a cause".
    - `@since 21`.
    - Source: [MatchException.java @ jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/lang/MatchException.java) **[src]**
  - Verified by separate compilation **[local]**:
    1. Compile `Status permits Active, Closed`, `enum Level { LOW, HIGH }` and `Client`.
    2. Recompile only the hierarchy as `permits Active, Closed, Frozen` and `Level { LOW, HIGH, CRITICAL }`.
    3. The old `Client` prints `sealed switch: java.lang.MatchException` and `enum switch: java.lang.MatchException`. Old values still work: `active`, `low`.
    4. Recompiling `Client` gives two "does not cover all possible input values" errors.
  - Pitfall seen on the way: copying only `Client.class` without the synthetic `Client$1.class` (the enum switch map) gave `NoClassDefFoundError: Client$1`.
- **The bytecode is not an instanceof chain** **[local]**. `javap -c` of `Client.label` shows:
  - `invokedynamic … #0:typeSwitch:(Ljava/lang/Object;I)I` (`java.lang.runtime.SwitchBootstraps`).
  - A synthetic arm `new java/lang/MatchException … invokespecial MatchException.<init>(String, Throwable)`.
- **Record patterns: nesting, var, generic inference, instanceof, flow scoping** **[local]**. All of these compile and run on 21:
  - `case Line(Point(var x1, var y1), Point(int x2, int y2)) when x1 == x2 -> …`
  - `case Ok<T>(var v)` and `case Err<T>(var msg, var cause) when cause != null` over `sealed interface Result<T> permits Ok, Err`, exhaustive with no default.
  - `if (o instanceof Line(Point(var x1, var y1), var to) && x1 == 0 && y1 == 0)`
  - `if (!(o instanceof Point p)) return …; return "point with x=" + p.x();`, where the binding `p` is in scope after the negated test.
  - Outputs: `vertical at x=1 len 5`, `horizontal at y=3`, `ok [1, 2]`, `err boom caused by RuntimeException`, `from origin to Point[x=9, y=9]`, `point with x=3`, `not a point`.
- **Goetz/Bierman on exhaustiveness vs remainder**: an exhaustive pattern set leaves a "remainder" (null, novel subtypes), handled by the runtime. Already cited in the earlier notes — [exhaustiveness.md](https://raw.githubusercontent.com/openjdk/amber-docs/master/site/design-notes/patterns/exhaustiveness.md)
- **Amber 2026 guidance on `default` over sealed types** **[src]** — [exhaustiveness-guide.md](https://github.com/openjdk/amber-docs/blob/master/site/guides/exhaustiveness-guide.md)
  - "It is almost never necessary to use `default` when switching over a `sealed` type -- and often not the best option."
  - "By default, avoid `default`… it sweeps errors, both present and future, under the rug."
  - "If it is impractical to handle each permitted subtype with its own `case`, we should use the narrowest possible type pattern… a match-all `case`… It is not recommended to use a match-all `case` with a broader type pattern than the selector type, e.g., `case Object other`."
  - For nested sealed hierarchies, "totalize each branch explicitly", e.g. `case A other` rather than `case AB other`, "This preserves the ability for exhaustiveness checking of the `B` options".
  - On MatchException: "if a fruit appears that it is unprepared to deal with, we get feedback at run time… this is also good!"
- **Kotlin side, exact kotlinc 2.4.21 text** **[local]**:
  ```
  NonEx.kt:5:30: error: 'when' expression must be exhaustive. Add the 'is Rect' branch or an 'else' branch.
  Guard.kt:4:30: error: 'when' expression must be exhaustive. Add the 'is Circle' branch or an 'else' branch.
  ```
  - The second error comes from `is Circle if s.r > 0 -> …` with no unguarded `is Circle`: a guarded branch does not count toward exhaustiveness, which is the same rule as Java's `when`.
  - Kotlin docs: "If you use guard conditions in `when` expressions without an `else` branch, the compiler requires you to handle every possible case"; and "You can't use guard conditions when you have multiple conditions separated by a comma"; the runnable sample is marked `kotlin-min-compiler-version="2.2"`. — [control-flow.md](https://github.com/JetBrains/kotlin-web-site/blob/master/docs/topics/control-flow.md) **[src]**

### Inferences
- **javac 21 vs kotlinc:** kotlinc has named the missing branch for a long time. javac only gained "missing patterns:" in JDK 27. A lesson on 21 should show students how to read the bare error, and mention that 27+ lists the cases.
- **"Guards do not help exhaustiveness" holds in both languages.** Teach "always end a guarded family with an unguarded case of the same type".
- **The `null`-matching rule for nested type patterns is the subtlest point in this track.** Use the `Line(null, …)` demo.

### Gaps
- JDK 22–27 binaries were not available. Primitive-pattern behaviour (e.g. `case int i when i > 0` on an `Integer`/`long` selector, and exactness rules for `instanceof byte`) is documented only by feature status, not run.
- The text of JEP 530/532 is not available (openjdk.org blocked), so the exact "exactness" conversion rules are not quoted here.

---

## Key Question 5: What is data-oriented programming as Brian Goetz describes it, and how does it relate to Visitor and the expression problem?

### Takeaway
Data-oriented programming (DOP) in Java means:
- Model domain *data* as immutable, transparent product types (records) and sum types (sealed interfaces).
- Make illegal states unrepresentable, through types and validation in the canonical constructor.
- Write *operations* as functions that pattern-match over the data, not as virtual methods spread across the hierarchy.

This trades OO's easy "add a new type" for easy "add a new operation". The compiler checks exhaustiveness to make the trade safe. Goetz calls records, sealed classes and record patterns "the first feature arc"; carrier classes and reconstruction are the next one.

### Cited Findings
- **The first and next arcs.** "Records, sealed classes, and destructuring with record patterns constitute the first feature arc of 'data-oriented programming' for Java. After considering numerous design ideas, we're now ready to move forward with the next 'data oriented programming' feature arc: _carrier classes_ (and interfaces.)" — [beyond-records.md (Goetz, Jan 2026)](https://github.com/openjdk/amber-docs/blob/master/site/design-notes/beyond-records.md) **[src]**
- **Sum and product types.** "a data class is just an algebraic product type"; sealed types give sum types. "Both records and sealed types have a synergy with pattern matching; records admit easy decomposition into their components, and sealed types provide the compiler with exhaustiveness information so that a switch that covers all the subtypes need not provide a `default` clause." Also: "Pattern matching over tree nodes offers a more direct and flexible alternative to traversal than the Visitor pattern." — [records-and-sealed-classes.md (Goetz, 2019)](https://github.com/openjdk/amber-docs/blob/master/site/design-notes/records-and-sealed-classes.md) **[src]**
- **Visitor.** "if your language has sufficiently powerful pattern matching, the Visitor pattern is almost completely unnecessary". Already quoted with context in design_patterns.md — [pattern-matching-for-java.md](https://raw.githubusercontent.com/openjdk/amber-docs/master/site/design-notes/patterns/pattern-matching-for-java.md) **[src, earlier session]**
- **Sealed APIs evolve.** "A `sealed` type is an API that describes a hierarchy of permitted subtypes _at a single point in time_… adding new permitted subtypes later [should] be a permissible and compatible evolution." Clients get compile errors on recompile and `MatchException` at run time. "this is how we balance safety with resilience." — [exhaustiveness-guide.md](https://github.com/openjdk/amber-docs/blob/master/site/guides/exhaustiveness-guide.md) **[src]**
- **The four DOP principles from Goetz's InfoQ article (June 2022).** These are commonly quoted as:
  1. "Model the data, the whole data, and nothing but the data"
  2. "Data is immutable"
  3. "Validate at the boundary"
  4. "Make illegal states unrepresentable"
  - This is **[bg]**: infoq.com was blocked in both sessions, and the headings are from memory and secondary summaries. Verify against [InfoQ: Data Oriented Programming in Java](https://www.infoq.com/articles/data-oriented-programming-java/) before quoting.
- **Reconstruction mirrors the compact constructor.** "Careful readers will note a similarity between the transformation block of a `with` expression and the body of a compact constructor… the block is 'preloaded' with a set of component variables… upon normal completion of the block, those variables are passed to a canonical constructor". — [beyond-records.md](https://github.com/openjdk/amber-docs/blob/master/site/design-notes/beyond-records.md) **[src]**
- **Local lab demonstration** **[local]**:
  - The given Visitor (`Expr.accept` + `EvalVisitor`) and the pattern-matching `Exprs.eval` agree: `2 + 3 * -4` gives `-10`.
  - A nested-pattern `simplify` (`Neg(Neg(x))` gives `x`; `Mul(Num(0), _)` gives `0`; `Add(Num(0), r)` gives `r`; `Mul(Num(1), r)` gives `r`) is about 10 lines as a switch. As a Visitor it would need a double dispatch per nesting level.
  - See KQ9.

### Inferences
- **The expression problem, framed for a Kotlin engineer:**
  - OO, virtual methods, Visitor: adding a *type* is local; adding an *operation* touches every class, or every Visitor.
  - DOP, sealed + switch/when: adding an *operation* is a new function; adding a *type* breaks every exhaustive switch. The compiler lists every site (javac 27+ names the missing pattern; kotlinc always did).
  - Neither approach solves both. DOP is the right default for closed domain data: payments, events, ASTs, protocol messages. Keep virtual methods for open, plug-in hierarchies.
- **"Validate at the boundary" in Java means three things:**
  - the compact constructor (structural invariants),
  - parsing untrusted input into records at the edge,
  - pattern-matching on trusted records inside.
- Kotlin practice is the same, using `init {}` and sealed/data classes.

### Gaps
- Goetz's InfoQ article, dev.java's DOP tutorials, and inside.java Amber articles were all unreachable. The exact DOP principle wording and the article's examples are unverified **[bg]**.

---

## Key Question 6: Where is Project Valhalla heading, and what does it mean for records and for Kotlin value classes?

### Takeaway
- **Value objects** are instances of `value` classes. They are immutable, have no identity, and compare by field values.
- They are a **preview feature integrated into JDK 28** (in development, GA scheduled 2027-03-23). They are **not** in JDK 25, 26 or 27.
- `value record` is legal under the preview.
- Twenty-eight JDK classes become value classes when preview is on, including `Integer`, `Optional` and `LocalDate`.
- Null-restricted types are still Draft JEPs.
- Kotlin's `@JvmInline value class` (one field, compile-time erasure) was designed to make room for a future Valhalla-backed non-annotated `value class`. Kotlin has made no such change yet.

### Cited Findings
- **Definition and status.**
  - "*Value objects* are immutable objects that lack identity. They are distinguished solely by the values of their fields, and can be represented by Java Virtual Machines in ways that improve performance. Value objects will be available in JDK 28 as a preview feature."
  - "A value object is an instance of a *value class*, declared with the `value` modifier."
  - Source: [valhalla-docs value-objects.md](https://github.com/openjdk/valhalla-docs/blob/main/site/value-objects.md) **[src]**
- **JDK 28 optimisations and their limits** (same page) **[src]**:
  - "*reference flattening*, which reduces the memory footprint of value objects stored in fields and arrays, and *reference scalarization*, which avoids memory allocation for value objects in JIT-compiled code."
  - "Heap-flattened encodings are always read and written atomically, and need to account for `null` references. This means value objects with 64 bits or more of field data cannot normally be flattened."
  - "Scalarization does not happen until C2 compilation."
  - "Variables that are *polymorphic*… cannot be flattened and are not typically scalarized. This includes variables in generic APIs."
  - "For best performance, compile all classes that refer to a value class with `--enable-preview`."
  - Compatibility concerns: "serialization…, deep reflection (`java.lang.reflect.Field.setAccessible`), and garbage collection (`java.lang.ref` and `java.util.WeakHashMap`)."
- **Five feature sets, delivered incrementally:**
  1. Value Objects
  2. Null-Restricted Storage
  3. Array Enhancements
  4. Unifying Primitives and Classes
  5. Parametric JVM
  - Source: [_index.md](https://github.com/openjdk/valhalla-docs/blob/main/site/_index.md) **[src]**
- **JDK classes migrated under preview (master source).** 28 files carry the Javadoc line "When preview features are enabled, `{X}` is a value class":
  - `java.lang`: `Boolean`, `Byte`, `Character`, `Double`, `Float`, `Integer`, `Long`, `Short`
  - `java.time`: `Duration`, `Instant`, `LocalDate`, `LocalDateTime`, `LocalTime`, `MonthDay`, `OffsetDateTime`, `OffsetTime`, `Period`, `Year`, `YearMonth`, `ZonedDateTime`, and the four `java.time.chrono` dates (`HijrahDate`, `JapaneseDate`, `MinguoDate`, `ThaiBuddhistDate`)
  - `java.util`: `Optional`, `OptionalDouble`, `OptionalInt`, `OptionalLong`
  - `Integer`'s Javadoc: "Use of value class instances for synchronization or with object references result in `IdentityException`". The declaration reads `public final /*value*/ class Integer`, generated per `doc/value-class-preview.md`.
  - Source: [Integer.java @ master](https://github.com/openjdk/jdk/blob/master/src/java.base/share/classes/java/lang/Integer.java) (sparse clone, 2026-11-07) **[src]**
  - A news snippet speaks of "30 classes in the java.* APIs" **[search]**. The source count found here is 28, so treat ~30 as approximate.
- **New APIs, `@since 28`, preview** **[src]**:
  - `Class.isValue()`, annotated `@PreviewFeature(feature = PreviewFeature.Feature.VALUE_OBJECTS, reflective=true)`; it returns `false` when preview is off.
  - `java.lang.IdentityException`, annotated `@PreviewFeature(feature = …VALUE_OBJECTS)`.
  - Sources: [Class.java @ master](https://github.com/openjdk/jdk/blob/master/src/java.base/share/classes/java/lang/Class.java), [IdentityException.java @ master](https://github.com/openjdk/jdk/blob/master/src/java.base/share/classes/java/lang/IdentityException.java)
- **`value record` is accepted by javac on master.** Test sources contain `value record Point(int x, int y) {}`, `value record CheckSynchronizedRecord(int x, int y)`, and `value record ValueRecord() implements Serializable`. — [ValueObjectCompilationTests.java](https://github.com/openjdk/jdk/blob/master/test/langtools/tools/javac/valhalla/value-objects/ValueObjectCompilationTests.java), [CheckSynchronized.java](https://github.com/openjdk/jdk/blob/master/test/langtools/tools/javac/valhalla/value-objects/CheckSynchronized.java) **[src]**
- **New javac diagnostics on master** **[src]** — [compiler.properties @ master](https://raw.githubusercontent.com/openjdk/jdk/master/src/jdk.compiler/share/classes/com/sun/tools/javac/resources/compiler.properties):
  - "The identity type {1} cannot be a supertype of the value type {0}"
  - "'sealed' or 'non-sealed' modifiers are only applicable to abstract value classes"
  - "serializable value class does not declare, or inherits, a writeReplace method"
  - "use of a value-based class with an operation that expects reliable identity"
- **Records vs value classes (the design rationale).**
  - Goetz, 2019: "Value types are primarily about enabling _flat_ and _dense_ layout… In exchange for giving up _object identity_… With records, in exchange for giving up the ability to decouple a class's API from its representation, we gain a number of notational and semantic benefits… they are not the exact same trade. However, there are classes that may be willing to tolerate both restrictions… we might call these `value records`." — [records-and-sealed-classes.md](https://github.com/openjdk/amber-docs/blob/master/site/design-notes/records-and-sealed-classes.md) **[src]**
  - State of Valhalla: "While records have a lot in common with value classes -- they are final and their fields are final -- they are still identity classes… Value records combine the data-carrier idiom of records with the improved scalarization and flattening benefits of value classes." — [02-object-model.md](https://github.com/openjdk/valhalla-docs/blob/main/site/design-notes/state-of-valhalla/02-object-model.md) **[src]**
- **Kotlin value classes today.**
  - "Inline classes are a subset of value-based classes. They don't have an identity and can only hold values." On the JVM: `@JvmInline value class`; "An inline class must have a single property initialized in the primary constructor".
  - It is boxed when "used as generic type T", "used as type I" (an interface), or "used as Foo?". — [inline-classes.md](https://github.com/JetBrains/kotlin-web-site/blob/master/docs/topics/inline-classes.md) **[src]**
  - Local: `useIban(i: Iban)` compiles to `public static final int useIban-wD2u3So(java.lang.String)`, a mangled name with the erased parameter **[local]**.
- **Kotlin's stated Valhalla plan** (design notes, Elizarov, status "Under consideration"):
  - "The `@JvmInline` annotation makes it explicit that something special with this class is going on in JVM, and it enables us to support non-annotated value class in the future Valhalla JVM by compiling them using the capabilities of the Project Valhalla."
  - Multi-field value classes before Valhalla are "all theoretical".
  - The notes predate JEP 401 and use old Valhalla terms ("primitive classes"). — [KEEP notes/value-classes.md](https://raw.githubusercontent.com/Kotlin/KEEP/master/notes/value-classes.md) **[src]**
- **Null-restricted types.** "Null-Restricted Value Class Types (Preview)" (JEP draft 8316779) is listed as **Draft**. The general "Null-Restricted and Nullable Types (Preview)" (draft 8303099) is on the legacy page. — [_index.md](https://github.com/openjdk/valhalla-docs/blob/main/site/_index.md), [legacy.md](https://github.com/openjdk/valhalla-docs/blob/main/site/legacy.md) **[src]**
  - The HotSpot side already has internal null-restricted *storage*: `jdk.internal.value.ValueClass.isNullRestrictedField`, and C2 commits about "null-restricted source array". This is JDK-internal and has no language syntax. — [ValueClass.java @ master](https://github.com/openjdk/jdk/blob/master/src/java.base/share/classes/jdk/internal/value/ValueClass.java) **[src]**

### Inferences
- **For records:**
  - On JDK 28 with `--enable-preview`, adding `value` to a record whose identity you never rely on (no `==`, no `synchronized`, no weak references) is the intended path to flattening.
  - Records stay identity classes by default; no semantics change silently.
  - The 64-bit flattening limit means `record Money(long minor, String currency)` will not flatten under JDK 28's rules (more than 64 bits of fields, plus a reference). Small all-primitive records are the ones that benefit.
- **For Kotlin:**
  - Nothing changes until Kotlin ships a Valhalla compilation mode.
  - A Kotlin `data class` compiled today is an identity class on JDK 28.
  - `@JvmInline value class` stays a compile-time erasure trick.
  - Java's `value record` will be the first JVM-native multi-field value type.
- **Teaching line:** "Java 21–27: records are identity objects. JDK 28 preview: `value class`/`value record` give up identity for flattening, with atomicity and null limits. Null-restricted types are still drafts."

### Gaps
- The JEP 401 text (migration guidance, `==` semantics for value objects, "substitutability"), the JDK 28 EA build, and the value-objects JLS draft (download.java.net) were not reachable. **No value-class code was run.**
- What `==` means for value objects (it compares field values; Valhalla calls this "substitutability") is **[bg]**.
- Whether JetBrains has announced a Kotlin plan for JEP 401 after July 2026: no source was found in the Kotlin docs or KEEP.

---

## Key Question 7: How do these map to Kotlin, and what is honestly better on each side?

### Takeaway
- **Kotlin is better at:**
  - copying (built-in `copy`, vs Java's hand-written withers until JEP 468 ships)
  - concise sealed hierarchies with `data object`
  - smart casts on any `is` check
  - earlier and clearer exhaustiveness diagnostics
- **Java is better at:**
  - real **nested deconstruction patterns** in `switch`/`instanceof`, with guards over deconstructed components
  - JVM-level transparency (records serialize through the canonical constructor; reflection via `getRecordComponents`)
  - a defined run-time story for separate compilation (`MatchException`)
  - a direct path to Valhalla `value record`
- Kotlin destructuring is still positional `componentN()`, with name-based destructuring Experimental since 2.3.20.

### Cited Findings
| Concern | Java (21 → 28) | Kotlin 2.4.x | Evidence |
|---|---|---|---|
| Data carrier | `record` (final, all-component equality, no instance fields outside the header) | `data class`: only primary-constructor properties count for `equals`/`hashCode`/`toString`/`copy`; "Data classes can't be abstract, open, sealed, or inner" | [Record.java](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/lang/Record.java); [data-classes.md](https://github.com/JetBrains/kotlin-web-site/blob/master/docs/topics/data-classes.md) **[src]** |
| Body properties | Not allowed (`field declaration must be static`) **[local]** | Allowed, and **excluded** from generated members: "two `Person` objects with the same `name` but different `age` values are considered equal" | data-classes.md **[src]** |
| Copy / wither | Hand-written `withX`; JEP 468 `with {}` on hold | `copy(name = …)`: "creates a _shallow_ copy"; runs `init` validation (`copy() runs init validation: amount must be positive: -1`) **[local]** | data-classes.md **[src]**, local |
| Shallow copy trap | Same: `List` components are shared unless `List.copyOf` **[local]** | `c2 = c1.copy(id="c2"); c2.tags += "shared!"` gives `c1.tags=[a, shared!]` **[local]** | local |
| Destructuring | Record patterns, nested, in `switch`/`instanceof`, with guards over the bound parts | Positional `val (a, b) = x` via `componentN()`, no nesting in `when`. `val (amount2, id2) = p` **silently swaps** (no warning on 2.4.21) **[local]**. Name-based destructuring is **Experimental** (2.3.20+), with `-Xname-based-destructuring=only-syntax\|name-mismatch\|complete`; `complete` also adds `val [x, y] = pair` positional syntax | [destructuring-declarations.md](https://github.com/JetBrains/kotlin-web-site/blob/master/docs/topics/destructuring-declarations.md), [whatsnew2320.md](https://github.com/JetBrains/kotlin-web-site/blob/master/docs/topics/whatsnew/whatsnew2320.md) **[src]**; KEEP-0438 status "Working on the implementation, it's not public yet" — [KEEP-0438](https://raw.githubusercontent.com/Kotlin/KEEP/main/proposals/KEEP-0438-name-based-destructuring.md) **[src]** |
| Sum types | `sealed interface … permits` (inferable in one file), `non-sealed` | `sealed interface/class`, `data object`; subclasses in the same package and module | sealed-classes.md **[src]** |
| Exhaustive dispatch | `switch` with type/record patterns; error text on 21 is generic; 27+ lists missing patterns | `when` with `is`; names the missing branch: "'when' expression must be exhaustive. Add the 'is Rect' branch or an 'else' branch." **[local]** | KQ4 |
| Guards | `case T t when cond` (21) | `is T if cond` (stable since 2.2); not allowed with comma-separated conditions | [control-flow.md](https://github.com/JetBrains/kotlin-web-site/blob/master/docs/topics/control-flow.md) **[src]** |
| Smart cast | Pattern variable binding only (`instanceof T t`), flow-scoped | Smart casts after any `is` check on stable values | (Kotlin [typecasts.md](https://github.com/JetBrains/kotlin-web-site/blob/master/docs/topics/typecasts.md); not quoted) |
| Null in dispatch | `switch` throws NPE unless `case null`; nested type patterns match null | `when (x)` on a nullable subject needs `null ->` or `else` for exhaustiveness | KQ4 local; Kotlin side **[bg]** |
| Interop | Kotlin sees record components as properties (`newPerson.name`) | `@JvmRecord data class` emits a real record: "The class cannot explicitly inherit any other class (including `Any`)… cannot declare any mutable properties with backing fields"; "Applying `@JvmRecord` to an existing class is not a binary compatible change" | [jvm-records.md](https://github.com/JetBrains/kotlin-web-site/blob/master/docs/topics/jvm/jvm-records.md) **[src]**; `Point::class.java.isRecord == true`, accessor `x` **[local]** |
| Value types | JDK 28 preview `value class`/`value record` (JVM flattening) | `@JvmInline value class`, one property, erased/mangled (`useIban-wD2u3So`) | KQ6 |

- **Kotlin release context.** Kotlin 2.4.0 was released July 14, 2026, and 2.4.20 on September 7, 2026 — [whatsnew24.md](https://github.com/JetBrains/kotlin-web-site/blob/master/docs/topics/whatsnew/whatsnew24.md), [whatsnew2420.md](https://github.com/JetBrains/kotlin-web-site/blob/master/docs/topics/whatsnew/whatsnew2420.md) **[src]**. kotlinc 2.4.21 was used locally. Maven Central shows 2.5.0-Beta2 as the newest (lastUpdated 2026-10-21) — [kotlin-stdlib metadata](https://repo1.maven.org/maven2/org/jetbrains/kotlin/kotlin-stdlib/maven-metadata.xml) **[src]**
- **The "same rule" demo.** The Kotlin generated bytecode for `data class Pending` has `component1()`, `component2()`, `copy(String, long)` and `copy$default(...)` **[local]**. This parallels Java's accessors and canonical constructor.

### Inferences
- **What to say honestly to a Kotlin engineer:**
  - "You lose `copy()`, so write withers or a builder for wide records."
  - "You gain deconstruction patterns. `case Charge(Money(long m, var ccy), Card(var net, var corp), var r) when corp ->` has no Kotlin equivalent short of nested `is` checks plus smart casts."
  - "The exhaustiveness semantics are the same; Java adds a run-time `MatchException` for binary-incompatible changes, while Kotlin's `when` throws `NoWhenBranchMatchedException` **[bg]**."
- **Positional destructuring is a real Kotlin footgun** (the silent swap demo). Java's record patterns are also positional, but they are type-checked: a type pattern `String id` in the `long` position fails to compile. `var`-only patterns can still swap.

### Gaps
- The Kotlin runtime exception for a non-exhaustive `when` under separate compilation (`NoWhenBranchMatchedException`) was not demonstrated here **[bg]**.
- Kotlin nullable-subject `when` exhaustiveness was not compiled.
- Name-based destructuring was not compiled (Experimental flag; not tried).

---

## Key Question 8: Which misconceptions should lessons address, and with what evidence?

### Takeaway
Each misconception below has a one-command demo and a primary-source quote. The two most damaging in production are "records are deeply immutable" (lost `HashSet` keys, leaked state) and "`default` makes a sealed switch future-proof" (it hides the compile errors that sealing exists to give you).

### Cited Findings
- **"Records are value types."**
  - False on JDK 16–27: `new D(1.0) == new D(1.0)` is `false`, and `synchronized` on a record works **[local]**.
  - Goetz: records and value types "are not the exact same trade" — [records-and-sealed-classes.md](https://github.com/openjdk/amber-docs/blob/master/site/design-notes/records-and-sealed-classes.md) **[src]**.
  - State of Valhalla: records "are still identity classes" — [02-object-model.md](https://github.com/openjdk/valhalla-docs/blob/main/site/design-notes/state-of-valhalla/02-object-model.md) **[src]**.
  - `value record` exists only under the JDK 28 preview (KQ6).
- **"Records are always deeply immutable."**
  - The Javadoc says "shallowly immutable" — [Record.java](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/lang/Record.java) **[src]**.
  - Demos **[local]**: the list mutation changes `toString`/`hashCode`; a mutated `HashSet` key is lost; arrays compare by reference.
- **"Overriding the accessor hides the data."** False: the generated `toString` still prints the raw field (`Masked[card=4111111111111111]`), and equality breaks the copy invariant **[local]**.
- **"Sealed means final."**
  - A sealed type has permitted subtypes.
  - `non-sealed` re-opens a branch (`Custom.class.isSealed() == false`).
  - A concrete sealed class can be instantiated, which is why the subtypes alone are not exhaustive **[local]**.
- **"Switch patterns are just syntax sugar for instanceof chains."** The chain that forgets `Rect` compiles silently, while the switch gets "does not cover all possible input values". There are also:
  - dominance errors,
  - `invokedynamic typeSwitch` bytecode,
  - a synthetic `MatchException` arm,
  - defined `case null` semantics.
  - All shown **[local]**.
- **"A `default` makes the sealed switch future-proof."** Amber guide: "A `default` label is almost never the right answer… it sweeps errors, both present and future, under the rug… a `default` is not a true catch-all: it does not handle a `null` selector." — [exhaustiveness-guide.md](https://github.com/openjdk/amber-docs/blob/master/site/guides/exhaustiveness-guide.md) **[src]**
- **"An exhaustive switch can never fail at run time."** False: separate compilation gives `MatchException` for both sealed and enum switches **[local]**. A nested `R(null)` falls through record patterns (see the `MatchException` Javadoc) **[src]**.
- **"Valhalla is in JDK 25."** False. JEP 401 was integrated 2026-07-31 into JDK 28 mainline as a preview; JDK 25/26/27 `Preview.java` lists only `PRIMITIVE_PATTERNS` **[src]**.
- **"Withers shipped in JDK 23/24/25."** False. There is no implementing commit, and Goetz (Jan 2026) says JEP 468 is "on hold" **[src]**.
- **"Primitive patterns are final in JDK 25 LTS."** False. They are preview in 23–27, and still preview on master **[src]**.
- **"`_` works on Java 21."** Only with `--enable-preview` (exact error above) **[local]**. It is final in 22.
- **"Kotlin destructuring is by name."** It is positional. `val (amount2, id2) = p` silently swaps **[local]**. Name-based destructuring is Experimental (2.3.20+) **[src]**.

### Inferences
- Order the misconceptions by lesson. A suggested mapping is in Teaching notes.

### Gaps
- None beyond those in KQ1–KQ7.

---

## Key Question 9: Which lab exercises are gradable with JUnit on Java 21, and what are the expected outcomes?

### Takeaway
Four labs were written as reference solutions with an 11-test JUnit suite. They compile with `javac --release 21` and **all 11 tests pass** on JUnit Platform 6.1.3. One test uses `javax.tools.JavaCompiler` to *prove* that adding a state breaks an exhaustive switch. That turns a compile-time property into a gradable JUnit assertion.

### Cited Findings (all **[local]** unless noted)
- **Setup used.**
  - `javac --release 21 -d out/main src/lab/*.java`
  - `java -jar junit-platform-console-standalone-6.1.3.jar execute --class-path out/main:out/test --select-class lab.LabTests`
  - The labs repo also pins JUnit 6.1.3, AssertJ 3.27.7, Kotlin 2.4.21 and `options.release.set(21)` in `labs/build.gradle.kts` (read locally).
  - JUnit metadata: [junit-platform-console-standalone maven-metadata](https://repo1.maven.org/maven2/org/junit/platform/junit-platform-console-standalone/maven-metadata.xml) shows latest 6.1.3 **[src]**.
  - Result: `11 tests successful, 0 tests failed`.
- **Lab 1: payment lifecycle as a sealed interface of records with an exhaustive switch.**
  - Model: `sealed interface Payment permits Created, Authorized, Captured, Refunded, Failed` (nested records) and `sealed interface Command permits Authorize, Capture, Refund, Decline`.
  - `Lifecycle.apply(Payment, Command)` is a nested switch with no `default`. It uses record patterns, e.g. `case Captured(var id, Money(long minor, var ccy)) -> switch (c) { case Refund(long r) when r > 0 && r <= minor -> new Refunded(id, new Money(r, ccy)); case Refund r -> throw new IllegalArgumentException(...); … }`.
  - Tests:
    - **happyPath**: `Created → Authorize("A1") → Capture → Refund(400)` equals `new Refunded("p1", new Money(400, "EUR"))`, and `isTerminal` is true.
    - **illegalTransitionsThrow**: `Capture` on `Created` gives `IllegalStateException`; `Refund(5_000)` on `Captured(1_000)` gives `IllegalArgumentException`; any command on `Failed` gives `IllegalStateException`.
    - **addingAStateBreaksTheBuild**: compiles, in-process, a client switching over `S permits A, B, C` that only handles `A` and `B`. It asserts exactly one error containing "does not cover all possible input values". This passes on 21 and stays valid on 27+, whose message starts with the same text.
  - Teaching note from building it: on 21 the "other commands" arm cannot be `case Capture _x, Refund _y ->` ("illegal fall-through from a pattern"), so each case is listed separately. On 22+, use `case Capture _, Refund _ ->`.
- **Lab 2: validation with compact constructors.**
  - `record Money(long minor, String currency)` trims and upper-cases the currency, requires `[A-Z]{3}`, and rejects negative amounts. `Created` takes `lineItems = List.copyOf(lineItems)` and rejects empty lists.
  - Tests:
    - `new Money(1, " eur ").currency()` equals `"EUR"`.
    - `-1` gives `IllegalArgumentException`; `"EURO"` gives `IllegalArgumentException`; `null` gives `NullPointerException`.
    - Mutating the caller's list after construction leaves `lineItems()` equal to `[book]`.
    - `lineItems().add` gives `UnsupportedOperationException`.
    - `new Money(5,"usd")` equals `new Money(5,"USD")`, and the hashCodes match.
  - Normalisation in the compact constructor makes `equals` agree with business equality.
- **Lab 3: replace a Visitor with pattern matching.**
  - Given: `Expr` with `accept(Visitor<R>)` and an `EvalVisitor`.
  - Students write `Exprs.eval`, `Exprs.show` and `Exprs.simplify` with exhaustive switches.
  - Tests:
    - Parity with the visitor: `2 + 3 * -4` gives `-10`.
    - `show` gives `"(2 + 3 * -4)"`.
    - `simplify(Neg(Neg(Num 7)))` gives `Num 7`.
    - `simplify(Mul(Num 0, e))` gives `Num 0`.
    - `simplify(Add(Num 0, Mul(Num 1, Num 5)))` gives `Num 5`.
- **Lab 4: fee calculator using record patterns with guards.**
  - Model: `record Charge(Money amount, Method method, Region region)`, `sealed interface Method permits Card, BankTransfer, Wallet`, `record Card(Network network, boolean corporate)`.
  - The rules are ordered so that the guards matter: AMEX first, then corporate. The switch is exhaustive with no `default`.
  - Expected fees for 10,000 minor units:

    | Charge | Fee |
    |---|---|
    | AMEX/EEA | 350 |
    | VISA corporate/EEA | 290 |
    | VISA consumer/EEA | 30 |
    | MASTERCARD consumer/UK | 30 |
    | VISA consumer/US | 150 |
    | instant transfer | 50 |
    | normal transfer | 20 |

  - Wallet: 999 gives 0; 1,000 gives 10 (boundary).
  - Rounding down: 33 minor at 30 bps gives 0.
  - Key pattern: `case Charge(Money(long m, var ccy), Card(var net, var corp), var r) when net == Network.AMEX -> bps(m, 350);`

### Inferences
- **Graders can enforce "no `default` over sealed types" in two ways:**
  - a source scan, or
  - Lab 1's compiler-API trick: compile the student's switch against a hierarchy with one extra permitted subtype, and expect the error.
- **Good mutation-style extra tests:**
  - Add `record Chargeback(...) implements Payment` and check that the build breaks.
  - Swap the AMEX and corporate cases, and check that `fee(AMEX corporate)` changes from 350 to 290.

### Gaps
- The Gradle build in `labs/` was not run (to avoid writing into the course repo). Only the standalone JUnit console run was done.
- A Kotlin twin of each lab (data classes plus `when` guards) was not packaged as tests here, though each Kotlin construct was compiled in KQ7.

---

## Verified URLs

Only pages actually fetched in this session (via curl/raw, git clone, or sparse clone). The git-clone-read files are given as their github.com blob/commit URLs: the contents were read from the clone, because github.com HTML pages were blocked.

**OpenJDK source (raw.githubusercontent.com, HTTP 200)**
- https://raw.githubusercontent.com/openjdk/jdk/jdk-21-ga/src/java.base/share/classes/jdk/internal/javac/PreviewFeature.java (and the same path at jdk-22-ga, jdk-23-ga, jdk-24-ga, jdk-25-ga, jdk-26-ga, jdk-27-ga, master)
- https://raw.githubusercontent.com/openjdk/jdk/jdk-21-ga/src/jdk.compiler/share/classes/com/sun/tools/javac/code/Preview.java (and 22…27-ga, master)
- https://raw.githubusercontent.com/openjdk/jdk/master/src/jdk.compiler/share/classes/com/sun/tools/javac/code/Source.java (also fetched at 21…27-ga)
- https://raw.githubusercontent.com/openjdk/jdk/jdk-27-ga/make/conf/version-numbers.conf (and 21…26-ga, master)
- https://raw.githubusercontent.com/openjdk/jdk/jdk-26-ga/src/jdk.compiler/share/classes/com/sun/tools/javac/resources/compiler.properties
- https://raw.githubusercontent.com/openjdk/jdk/jdk-27-ga/src/jdk.compiler/share/classes/com/sun/tools/javac/resources/compiler.properties
- https://raw.githubusercontent.com/openjdk/jdk/master/src/jdk.compiler/share/classes/com/sun/tools/javac/resources/compiler.properties
- https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/lang/Record.java
- https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/lang/runtime/ObjectMethods.java
- https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/lang/MatchException.java
- https://raw.githubusercontent.com/openjdk/valhalla/lworld/src/java.base/share/classes/jdk/internal/javac/PreviewFeature.java (plus `lworld` version-numbers.conf and Source.java)

**OpenJDK master via sparse git clone (2026-11-07, commit c73d7d1)**
- https://github.com/openjdk/jdk/blob/master/src/java.base/share/classes/java/lang/Integer.java (and the other 27 "value class when preview" files listed in KQ6)
- https://github.com/openjdk/jdk/blob/master/src/java.base/share/classes/java/lang/Class.java
- https://github.com/openjdk/jdk/blob/master/src/java.base/share/classes/java/lang/IdentityException.java
- https://github.com/openjdk/jdk/blob/master/src/java.base/share/classes/jdk/internal/value/ValueClass.java
- https://github.com/openjdk/jdk/blob/master/test/langtools/tools/javac/valhalla/value-objects/ValueObjectCompilationTests.java
- https://github.com/openjdk/jdk/blob/master/test/langtools/tools/javac/valhalla/value-objects/CheckSynchronized.java

**OpenJDK commits (messages and diffs read from a treeless git clone of master history)**
- https://github.com/openjdk/jdk/commit/cc278dbb8a1ca0754d5842708b9029441055d361 (JEP 401 + 539, 2026-07-31)
- https://github.com/openjdk/jdk/commit/84e8787d1fdfe2d92f8b2c9b959651d8d63be91b (JDK-8367530 missing-patterns diagnostics, 2026-02-04; diff of tests read)
- https://github.com/openjdk/jdk/commit/99135d2e05bb501fe9f9f0d36abd25894d0f93de (JEP 530)
- https://github.com/openjdk/jdk/commit/6811a11e278118b8b2781f1eaf45d363a3d2db49 (JEP 488)
- https://github.com/openjdk/jdk/commit/1733d2ea244756238c302d802511eb1557cd46ac (JEP 455)
- https://github.com/openjdk/jdk/commit/af87035b713f8bfe05a007a4d4670cefc6a6aaf2, https://github.com/openjdk/jdk/commit/c55287d197ef024033f8dfbb5a365cb091bc67fb, https://github.com/openjdk/jdk/commit/ca52afa38e47bf1c901d05a817fe76d440bff2bd (start of JDK 26/27/28)
- https://github.com/openjdk/jdk/commit/83c9689bd612e82904db959dcf8c9cc08e45e210, https://github.com/openjdk/jdk/commit/ee4d42c8fae5cd57e484d19d06e26c013f04486c, https://github.com/openjdk/jdk/commit/5ccf99b8e921269d7e8deedbd9b8bdd131d91f3a, https://github.com/openjdk/jdk/commit/2e68b79a3973c8a3dde6b47f19b19c0c7faacc51, https://github.com/openjdk/jdk/commit/87a47721981bb84b1e22b5b2d8d24bc60c8b7223, https://github.com/openjdk/jdk/commit/3c0d1f5294b2d430c1d9f0f6aedd2f68149f9c19

**Amber design notes (git clone of openjdk/amber-docs @ 058be2f, 2026-08-14)**
- https://github.com/openjdk/amber-docs/blob/master/site/design-notes/beyond-records.md (Goetz, Jan 2026)
- https://github.com/openjdk/amber-docs/blob/master/site/guides/exhaustiveness-guide.md (Bimpoudis, Buckley, Goetz, 2026-08-11)
- https://github.com/openjdk/amber-docs/blob/master/eg-drafts/reconstruction-records-and-classes.md (Goetz, Aug 2020)
- https://github.com/openjdk/amber-docs/blob/master/site/design-notes/records-and-sealed-classes.md (Goetz, 2019)

**Valhalla docs (git clone of openjdk/valhalla-docs @ f86e731, 2026-08-08)**
- https://github.com/openjdk/valhalla-docs/blob/main/site/_index.md
- https://github.com/openjdk/valhalla-docs/blob/main/site/value-objects.md
- https://github.com/openjdk/valhalla-docs/blob/main/site/early-access.md
- https://github.com/openjdk/valhalla-docs/blob/main/site/legacy.md
- https://github.com/openjdk/valhalla-docs/blob/main/site/design-notes/state-of-valhalla/02-object-model.md

**Kotlin (sparse git clone of JetBrains/kotlin-web-site @ 2e7cf89, 2026-11-06; rendered at kotlinlang.org/docs/<name>.html)**
- https://github.com/JetBrains/kotlin-web-site/blob/master/docs/topics/data-classes.md
- https://github.com/JetBrains/kotlin-web-site/blob/master/docs/topics/sealed-classes.md
- https://github.com/JetBrains/kotlin-web-site/blob/master/docs/topics/control-flow.md
- https://github.com/JetBrains/kotlin-web-site/blob/master/docs/topics/inline-classes.md
- https://github.com/JetBrains/kotlin-web-site/blob/master/docs/topics/destructuring-declarations.md
- https://github.com/JetBrains/kotlin-web-site/blob/master/docs/topics/jvm/jvm-records.md
- https://github.com/JetBrains/kotlin-web-site/blob/master/docs/topics/whatsnew/whatsnew2320.md, https://github.com/JetBrains/kotlin-web-site/blob/master/docs/topics/whatsnew/whatsnew24.md, https://github.com/JetBrains/kotlin-web-site/blob/master/docs/topics/whatsnew/whatsnew2420.md
- https://raw.githubusercontent.com/Kotlin/KEEP/master/notes/value-classes.md
- https://raw.githubusercontent.com/Kotlin/KEEP/main/proposals/KEEP-0438-name-based-destructuring.md
- https://kotlinlang.org/docs/data-classes.html (HTTP 200 reachability check only; the content was read from the GitHub source above)

**Other**
- https://raw.githubusercontent.com/projectlombok/lombok/master/doc/changelog.markdown
- https://repo1.maven.org/maven2/org/projectlombok/lombok/maven-metadata.xml
- https://repo1.maven.org/maven2/org/junit/platform/junit-platform-console-standalone/maven-metadata.xml (and the 6.1.3 jar)
- https://repo1.maven.org/maven2/org/jetbrains/kotlin/kotlin-stdlib/maven-metadata.xml
- https://github.com/JetBrains/kotlin/releases/download/v2.4.21/kotlin-compiler-2.4.21.zip (downloaded and used)

**Seen only in search results (NOT fetched; [search])**
- https://openjdk.org/jeps/468, https://openjdk.org/jeps/507, https://inside.java/2025/06/17/jep507-target-jdk25/, https://inside.java/2026/05/08/jep532-target-jdk27/, https://mail.openjdk.org/pipermail/jdk-dev/2024-February/008744.html, https://mail.openjdk.org/pipermail/amber-dev/2025-May/009295.html, https://infoq.com/news/2026/08/jep401-value-objects-preview

**Attempted but blocked:** openjdk.org/jeps/*, docs.oracle.com (JLS 25), inside.java, dev.java, infoq.com (Goetz DOP article), bugs.openjdk.org, cr.openjdk.org, mail.openjdk.org, jdk.java.net (EA builds), github.com commit/release HTML pages, Adoptium release pages, api.github.com.

---

## Teaching notes

### Suggested 4-lesson split
1. **Records as transparent carriers.** Topics:
   - canonical, compact and non-canonical constructors (and JDK 25 flexible constructor bodies)
   - equality semantics (NaN/-0.0/arrays)
   - shallow immutability and `List.copyOf`
   - serialization through the canonical constructor (the tamper demo)
   - javap/ObjectMethods
   - accessor-override masking trap
   - withers by hand vs Kotlin `copy`, and JEP 468's status
   - Lombok positioning
2. **Sealed hierarchies.** Topics:
   - `permits`/inference
   - final/sealed/non-sealed
   - module/package rule (the unnamed-module error demo)
   - concrete sealed classes
   - sum + product = ADT
   - documenting why a type is sealed (Amber guide)
   - Kotlin sealed/`data object`
3. **Pattern matching.** Topics:
   - `instanceof` flow scoping
   - switch patterns, guards and dominance
   - `case null`
   - record patterns (nested, generic inference)
   - exhaustiveness errors (21 text vs 27 "missing patterns")
   - `MatchException` under separate compilation
   - `_` (preview on 21, final on 22)
   - primitive patterns (preview through 27)
   - Kotlin `when` + guards + smart casts + positional destructuring
4. **Data-oriented programming and the road ahead.** Topics:
   - Goetz's principles
   - the expression problem
   - Visitor → switch refactor
   - the "avoid `default`" guidance
   - carrier classes and pattern assignment (design stage)
   - Valhalla: JEP 401 in the JDK 28 preview, `value record`, flattening limits, Kotlin `@JvmInline`

### Misconceptions, mapped to lessons and demos
- **Lesson 1:**
  - "records are value types" (`==`/`synchronized` demo)
  - "records are deeply immutable" (lost `HashSet` key)
  - "overriding the accessor hides data" (`Masked` toString)
  - "withers shipped" (no commit; "on hold")
- **Lesson 2:** "sealed means final" (`non-sealed` + `isSealed()` + concrete sealed class error)
- **Lesson 3:**
  - "switch patterns are instanceof sugar" (silent if-chain vs error; `typeSwitch` bytecode; `MatchException`)
  - "`default` future-proofs a switch" (Amber guide)
  - "exhaustive means never fails" (separate compilation demo)
  - "`_` works on 21" (preview error text)
  - "Kotlin destructures by name" (silent swap)
- **Lesson 4:**
  - "Valhalla is in JDK 25" (Preview.java at 25/26/27 vs master; commit date 2026-07-31 after the 2026-06-04 fork)
  - "primitive patterns are final" (preview 23–27)

### Analogies (for a Kotlin engineer)
- **record ≈ `data class` with `val`-only header properties.** Differences: no body state, no `copy`, final, and serialization goes through the constructor.
- **`sealed interface … permits`** ≈ `sealed interface`. **`non-sealed`** ≈ an `open` subclass of a sealed parent.
- **`switch` with record patterns** ≈ `when` with `is` + smart cast, except that Java can destructure nested components in the label itself and guard on them.
- **`MatchException`** ≈ Kotlin's `NoWhenBranchMatchedException` **[bg]**: both are the run-time backstop of an exhaustive match.
- **JDK 28 `value record`** ≈ what Kotlin's `@JvmInline value class` wants to be when it grows up: multi-field, identity-free, JVM-flattened.

### Demos with expected outputs (all reproduced on javac/java 21.0.12.1, `--release 21`)
- **Non-exhaustive sealed switch:** `error: the switch expression does not cover all possible input values` (expression) and `error: the switch statement does not cover all possible input values` (statement).
- **Dominance:** `error: this case label is dominated by a preceding case label`, for:
  - `String` after `CharSequence`
  - a guarded case after an unguarded one
  - a constant after an unguarded type pattern
  - a pattern after `default:`
- **Compact constructor:** `Money[minor=1250, currency=EUR]`, `IAE: negative amount: -1`, `NPE: currency`.
- **Nested record patterns:** `vertical at x=1 len 5`, `horizontal at y=3`, `diagonal Point[x=0, y=0]->Point[x=2, y=2]`. A null component falls to the type-pattern case: `diagonal null->Point[x=1, y=1]`.
- **javap of a record:** one `ObjectMethods.bootstrap` entry with arguments `Point`, `x;y`, `REF_getField Point.x:I`, `REF_getField Point.y:I`.
- **Separate compilation:** `sealed switch: java.lang.MatchException` and `enum switch: java.lang.MatchException`. (Copy all `Client*.class` files, or you get `NoClassDefFoundError: Client$1`.)
- **Serialization tamper:** `java.io.InvalidObjectException: lo > hi: 5 > 1 / cause: java.lang.IllegalArgumentException: lo > hi: 5 > 1`.
- **Kotlin (2.4.21):**
  - `'when' expression must be exhaustive. Add the 'is Rect' branch or an 'else' branch.`
  - `copy() runs init validation: amount must be positive: -1`
  - `shallow copy: c1.tags=[a, shared!]`
  - `swapped names: amount2=p1 id2=500`

### Lab exercises (expected outcomes verified; see KQ9)
1. **Payment lifecycle.** Sealed records plus an exhaustive nested switch. Includes a compiler-API test proving that adding a state breaks the build.
2. **Compact-constructor validation.** Normalisation, ISO currency, non-negative amounts, `List.copyOf` line items.
3. **Visitor → patterns.** Parity, plus a nested-pattern `simplify`.
4. **Fee calculator.** Record patterns with ordered guards. Expected fees: 350/290/30/30/150/50/20/0/10/0.

### Practical notes for lesson writers
- **Pin the toolchain in prose:**
  - "Java 21 (`--release 21`) unless marked."
  - Mark any 22+ syntax (`_`, `case A _, B _`) and any 25+ syntax (flexible constructor bodies) explicitly.
  - Mark primitive patterns and value classes as **preview** with the JDK version.
- **Quote javac errors with the JDK version.** The exhaustiveness text gains a "missing patterns:" tail from JDK 27, and JDK 28 will stop mentioning inaccessible types.
- **Do not use `case _ when …`.** javac 22–27 apparently accept it (inferred from the fix title), but JDK 28’s javac rejects it as non-JLS (JDK-8385488).
- **Do not promise JEP 468 syntax.** If you show `p with { x = 3; }`, label it "proposed, Candidate JEP, on hold as of Jan 2026".
- **Tie Kotlin claims to Kotlin 2.2+ (guards) and 2.4.x (tested).** Name-based destructuring needs the Experimental `-Xname-based-destructuring` flag (2.3.20+).
