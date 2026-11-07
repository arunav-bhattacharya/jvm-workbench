import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/kotlin/src"
P = "kotlin/workbench/kotlin/l02"
DK = "kotlin/workbench/kotlin/l02/demo"
DJ = "java/workbench/kotlin/l02/demo"
read = lambda p: (ROOT / p).read_text()
RUN = "./gradlew :kotlin:demo -Pmain=workbench.kotlin.l02.demo."


def demo(name):
    """Kotlin demo with its runnable Java twin."""
    return {"lang": "kotlin", "title": f"{name}.kt", "src": read(f"{lab}/demo/{DK}/{name}.kt"),
            "run": RUN + name + "Kt", "file": f"{lab}/demo/{DK}/{name}.kt",
            "alt": {"lang": "java", "title": f"{name}Java.java", "src": read(f"{lab}/demo/{DJ}/{name}Java.java"),
                    "run": RUN + name + "Java", "file": f"{lab}/demo/{DJ}/{name}Java.java"}}


FIG = (
    '<svg viewBox="0 0 680 300" role="img" aria-label="Where a Money value class stays a plain long and where the compiler boxes it into a Money object">'
    '<text class="t t-ok" x="170" y="28" text-anchor="middle">used as Money: a plain long</text>'
    '<text class="t t-bad" x="510" y="28" text-anchor="middle">used as another type: boxed</text>'
    '<rect class="box-ok" x="30" y="46" width="280" height="40" rx="8"/>'
    '<text class="t t-code" x="170" y="71" text-anchor="middle">val m: Money</text>'
    '<rect class="box-ok" x="30" y="96" width="280" height="40" rx="8"/>'
    '<text class="t t-code" x="170" y="121" text-anchor="middle">fun charge(m: Money)</text>'
    '<rect class="box-ok" x="30" y="146" width="280" height="40" rx="8"/>'
    '<text class="t t-code" x="170" y="171" text-anchor="middle">class Invoice(val m: Money)</text>'
    '<rect class="box-ok" x="30" y="196" width="280" height="40" rx="8"/>'
    '<text class="t t-code" x="170" y="221" text-anchor="middle">m + other, m == other</text>'
    '<rect class="box-bad" x="370" y="46" width="280" height="40" rx="8"/>'
    '<text class="t t-code" x="510" y="71" text-anchor="middle">fun &lt;T&gt; id(x: T)</text>'
    '<rect class="box-bad" x="370" y="96" width="280" height="40" rx="8"/>'
    '<text class="t t-code" x="510" y="121" text-anchor="middle">val m: Money?</text>'
    '<rect class="box-bad" x="370" y="146" width="280" height="40" rx="8"/>'
    '<text class="t t-code" x="510" y="171" text-anchor="middle">val p: Priced = m</text>'
    '<rect class="box-bad" x="370" y="196" width="280" height="40" rx="8"/>'
    '<text class="t t-code" x="510" y="221" text-anchor="middle">listOf(m), println(m)</text>'
    '<line class="ln-d" x1="340" y1="46" x2="340" y2="236"/>'
    '<text class="t-s t-m" x="170" y="264" text-anchor="middle">bytecode: long, constructor-impl, plus-hash</text>'
    '<text class="t-s t-m" x="510" y="264" text-anchor="middle">bytecode: Money.box-impl(long) first</text>'
    '<text class="t-s t-a" x="340" y="290" text-anchor="middle">the same rule as long and Long in Java</text>'
    '</svg>'
)

L = {
 "id": "kt-02",
 "title": "Value classes and what they compile to",
 "minutes": 35,
 "goal": "By the end you can write a validated value class, predict where it is a plain `long` and where it gets boxed, read its mangled names in `javap`, and give Java callers a safe way in.",
 "warmup": {
  "q": "`@JvmInline value class Money(val cents: Long)`. Which of these creates a `Money` object on the heap at run time?",
  "options": ["`val total = a + b`, where `a` and `b` are `Money`", "`listOf(a, b)`", "`class Invoice(val amount: Money)` when you build an `Invoice`", "None of them: a value class is never boxed"],
  "answer": 1,
  "why": "A `List` holds objects, so each element is boxed into a real `Money` (the compiler calls `Money.box-impl(long)`). Inside `Invoice` the property is stored as a `long` field, and `a + b` compiles to a static method on two longs. The last option is the common belief, and the docs say the opposite: value classes are boxed whenever they are used as another type."
 },
 "sections": [
  {
   "h": "A value class is a type at compile time and a long at run time",
   "body": "A `Long` parameter named `amountMinor` will accept an order id without complaint. Both are `Long`, so the compiler can't tell them apart. The classic fix is a small wrapper class, `class Cents(val value: Long)`, and it works, but every amount is now an extra object on the heap. Kotlin's **value class** keeps the wrapper's type safety and, wherever it can, drops the object: at run time only the wrapped value, the **underlying type** (`Long` here), is left. Here is the wrapper in both languages:\n\n```java\n// Java's closest shape today: a record. It's a real object, allocated on every new.\nrecord Cents(long value) {\n    Cents {\n        if (value < 0) throw new IllegalArgumentException(\"negative amount: \" + value);\n    }\n}\n```\n\n```kotlin\n@JvmInline\nvalue class Cents(val value: Long) {\n    init {\n        require(value >= 0) { \"negative amount: $value\" }\n    }\n\n    operator fun plus(other: Cents): Cents = Cents(value + other.value)\n\n    override fun toString(): String = \"$value cents\"\n}\n\nfun charge(amount: Cents): String = \"charged $amount\"\n\ncharge(199L)   // error: argument type mismatch: actual type is 'Long', but 'Cents' was expected.\n```\n\nThe rules are short. On the JVM you write `@JvmInline value class` with exactly one property in the primary constructor. You may add `init` blocks, functions, secondary constructors and properties without backing fields (so no `lateinit` and no delegation). A value class can implement interfaces, can't extend a class, and is always final.\n\nAt run time most of it disappears. `javap -p` on the demo shows what the compiler built:\n\n```text\npublic static final java.lang.String charge-X49TzF8(long);   // takes a plain long\npublic static long constructor-impl(long);                  // Cents(...) runs init here\npublic static final long plus-dpzqtSM(long, long);          // a member, now static on longs\npublic static final Cents box-impl(long);                   // used only when a box is needed\n```\n\n`Cents(150)` compiles to a call to `constructor-impl`, which runs your `init` block and returns the same `long`. No object is created. `plus` turned into a static method that adds two longs. The `Cents` class still exists, with one `long` field, for the moments when a real object is needed. That's the next section.\n\nCompare a type alias. `typealias CentsAlias = Long` gives you a second name and nothing else: the docs say aliases are assignment-compatible with their underlying type, and value classes are not. In the demo, an `orderId: Long` goes straight into `chargeAlias` and compiles. Use aliases to shorten long generic types. Use value classes where mixing up two values would be a bug.\n\nYou already use value classes from the standard library: `UInt`, `ULong`, `kotlin.time.Duration` and `kotlin.Result` are all declared this way, and `javap` shows the same `box-impl` and `unbox-impl` on each.",
   "try": {
    "title": "See what Cents compiles to",
    "minutes": 4,
    "steps": [
     "Run `ValueClassDemo` with the command below.",
     "From `labs/`, run `javap -p -cp kotlin/build/classes/kotlin/demo workbench.kotlin.l02.demo.ValueClassDemoKt workbench.kotlin.l02.demo.Cents`. Find `charge`, `constructor-impl` and `plus`.",
     "Uncomment the wrong move in `main`, predict the error, and run. Comment it out again.",
     "Run `ValueClassDemoJava`. Before you do, predict its second line: Java calls `chargeFromJava(-5L)`."
    ],
    "code": demo("ValueClassDemo"),
    "expect": "The Kotlin demo prints `charged 199 cents`, `charged 981 (alias)` and `rejected: negative amount: -1`. `javap` lists `charge-X49TzF8(long)`, `chargeFromJava(long)` and, on `Cents`, `constructor-impl(long)` and `plus-dpzqtSM(long, long)`. The wrong move fails with `argument type mismatch: actual type is 'Long', but 'Cents' was expected.` The Java twin prints `charged -5 cents`: Java passed a raw `long`, so `init` never ran. The last section explains that door."
   },
   "refs": [{"title": "Inline value classes (Kotlin docs)", "url": "https://kotlinlang.org/docs/inline-classes.html", "kind": "docs"}]
  },
  {
   "h": "Boxed whenever it is used as another type",
   "body": "Value classes do get **boxed**, which means wrapped in a real `Money` object on the heap, the way Java wraps a `long` in a `Long`. The rule fits in one line of the docs: inline classes are boxed whenever they are used as another type.\n\n```java\n// Java's long and Long follow the same rule: a primitive where it can, a box when it must\nstatic Object asGeneric(Object x) { return x; }\n\nlong minor = 1_999;\nObject boxed = asGeneric(minor);      // autoboxed into a Long object\nList<Long> list = List.of(minor);     // another Long object\n```\n\n```kotlin\nfun <T> asGeneric(x: T): Any? = x     // used as T: boxed\nfun asNullable(a: Amount?): Any? = a  // used as Amount?: boxed\nfun asInterface(p: Priced): Any = p   // used as Priced: boxed\n\nclass Invoice(val amount: Amount)     // used as Amount: stored as a long field\n```\n\nFour cases box: a generic type parameter, a nullable type (`Amount?` must be able to hold `null`, and a `long` can't), an interface the class implements, and anything typed `Any`, which includes every collection and `println`. In the bytecode each one shows up as a call to `Amount.box-impl(long)` right before the call that needs the object. So a `List<Money>` holds one `Money` object per element. The docs draw the same comparison you'd draw: it's like `Int` being either a primitive `int` or a `java.lang.Integer`.\n\nEquality still works by value. `a == Amount(1_999)` compiles to `equals-impl0(long, long)`, a comparison of two longs. Identity doesn't exist: `a === b` is a compile error, `identity equality for arguments of types 'Amount' and 'Amount' is prohibited.` That's stricter than Java, where `Long a = 1_999L, b = 1_999L; a == b` is `false` and the same code with `100L` is `true`, because small boxes are cached.\n\nIn practice, a value class saves the allocation wherever it's used as itself: fields, parameters, return values, arithmetic. That covers most domain code. A hot path that pushes millions of amounts through a `List<Money>` or a generic `Map` pays the same boxing as `List<Long>`. If that shows up in a profile, use a `LongArray`, as you would in Java.",
   "figure": {"svg": FIG, "caption": "Used as itself, a value class is its underlying long. Used as anything else, the compiler boxes it first."},
   "try": {
    "title": "Count the boxes",
    "minutes": 4,
    "steps": [
     "Run `BoxingDemo` and `BoxingDemoJava`. Predict each line before you look.",
     "From `labs/`, run `javap -c -p -cp kotlin/build/classes/kotlin/demo workbench.kotlin.l02.demo.BoxingDemoKt` and count the calls to `Amount.\"box-impl\"` in `main`.",
     "Uncomment the wrong move in `BoxingDemo.kt` and run it."
    ],
    "code": demo("BoxingDemo"),
    "expect": "The field in `Invoice` is a `long`. Every other line prints `Amount`, because generic, nullable, interface and list uses all box, and `javap` shows four `box-impl` calls in `main`, one before each of those calls. The equality line prints `true` through `equals-impl0`. The wrong move fails with `identity equality for arguments of types 'Amount' and 'Amount' is prohibited.` The Java twin prints `false` for `a == b` with 1,999 and `true` with 100: that's the Long cache, a trap Kotlin closes for value classes."
   }
  },
  {
   "h": "Mangled names keep Java out, and @JvmName lets it back in",
   "body": "Look at that name again: `charge-X49TzF8(long)`. The compiler adds a hash to every function that takes a value class. The docs call it mangling, and it does two jobs. It prevents clashes: `describe(key: IdempotencyKey)` and `describe(raw: String)` would both be `describe(String)` in the bytecode, and with mangling they become `describe-<hash>(String)` and `describe(String)`. And it keeps Java away from functions that expect a valid value: a `-` can't appear in a Java method name.\n\nIt reaches further than functions. A class with a value-class property gets a private constructor, plus a public synthetic one with an extra `DefaultConstructorMarker` parameter, and a mangled getter: the demo's `Invoice` has `getAmount-hwXtt_M()`. Java can't build it or read it by name. Members that return a value class are mangled too, so the lab's `Money.Companion.parse` becomes `parse-LC5NfZc(String)`. A top-level function that only returns one is not: `parseAmount(String)` hands Java a plain `long`.\n\nFor a single function, the quick fix is `@JvmName`:\n\n```java\nSystem.out.println(ValueClassDemoKt.chargeFromJava(199L));   // charged 199 cents\nSystem.out.println(ValueClassDemoKt.chargeFromJava(-5L));    // charged -5 cents: init never ran\n// ValueClassDemoKt.charge(199L);                            // error: cannot find symbol\n```\n\n```kotlin\n@JvmName(\"chargeFromJava\")\nfun chargeJava(amount: Cents): String = \"charged $amount\"\n```\n\nRead the second Java line again. Java passes a raw `long`, and nothing runs `init` on the way in. **`@JvmName` opens a door around your validation**, so a function meant for Java should validate again, for example by building a fresh `Cents(amount.value)`.\n\nKotlin 2.2.0 added a fuller answer, `@JvmExposeBoxed`. It is still Experimental in 2.4, so you opt in with `@OptIn(ExperimentalStdlibApi::class)`. On a class it adds a public constructor that runs `init`. On a function it adds a version that takes and returns the box, `describeFee(Fee)`, next to the mangled `describeFee-pUsR5hI(long)`. The compiler flag `-Xjvm-expose-boxed` does the same for a whole module.\n\n```java\nFee fee = new Fee(125);                              // a real constructor: init runs\nSystem.out.println(ExposeBoxedDemoKt.describeFee(fee.doubled()));\n```\n\n```kotlin\n@file:OptIn(ExperimentalStdlibApi::class)\n\n@JvmExposeBoxed\n@JvmInline\nvalue class Fee(val minor: Long) {\n    init { require(minor >= 0) { \"negative fee: $minor\" } }\n    fun doubled(): Fee = Fee(minor * 2)\n}\n\n@JvmExposeBoxed\nfun describeFee(fee: Fee): String = \"fee of ${fee.minor} minor units\"\n```\n\nFrameworks see the same bytecode Java does. Anything that finds getters by name through reflection, such as a JSON mapper or an ORM reading an entity, will meet `getAmount-hwXtt_M`. Check how your libraries handle that before you put value classes in DTOs or entities.",
   "try": {
    "title": "Open the door for Java, properly",
    "minutes": 4,
    "steps": [
     "Run `ExposeBoxedDemo`, then `ExposeBoxedDemoJava`.",
     "Run `javap -p -cp kotlin/build/classes/kotlin/demo workbench.kotlin.l02.demo.Fee workbench.kotlin.l02.demo.ExposeBoxedDemoKt`. Find the two `doubled` methods and the two `describeFee` methods.",
     "Delete the first line of `ExposeBoxedDemo.kt` (`@file:OptIn(...)`) and run. Put it back."
    ],
    "code": demo("ExposeBoxedDemo"),
    "expect": "Both print `fee of 250 minor units`, and the Java twin also prints `rejected: negative fee: -1`, so the public constructor ran `init`. `javap` shows `doubled-etMGDqA(long)` next to `Fee doubled()`, `describeFee-pUsR5hI(long)` next to `describeFee(Fee)`, and a public `Fee(long)` constructor. Without the opt-in, both annotations fail with `this declaration needs opt-in. Its usage must be marked with '@kotlin.ExperimentalStdlibApi' or '@OptIn(kotlin.ExperimentalStdlibApi::class)'`."
   },
   "refs": [{"title": "Calling Kotlin from Java: inline value classes", "url": "https://kotlinlang.org/docs/java-to-kotlin-interop.html", "kind": "docs"},
            {"title": "KEEP-0394: @JvmExposeBoxed", "url": "https://github.com/Kotlin/KEEP/blob/main/proposals/KEEP-0394-jvm-expose-boxed.md", "kind": "read"}]
  },
  {
   "h": "One field only, until Valhalla",
   "body": "Give a value class two properties and the compiler stops you: `value class must have exactly one primary constructor parameter.` So `Point(x, y)` or `Money(cents, currency)` can't be value classes on the JVM in Kotlin 2.4, and there is no hidden flag for it.\n\nThe limit comes from the JVM. Kotlin can erase a one-field class into its field because the JVM already has a `long`. A two-field value with no identity needs support from the JVM itself, which is Project Valhalla. JEP 401, value classes and objects for Java, is integrated into JDK 28 as a preview feature, and JDK 28 is still in development. The Kotlin team's design notes explain why `@JvmInline` is mandatory today: it marks the current compile-time trick, so that a plain `value class` without the annotation can later compile to real Valhalla value classes. They call multi-field value classes before Valhalla \"all theoretical\". No Kotlin release has a Valhalla mode yet.\n\nFor now, the one-field limit shapes your design. An amount that carries its own currency stays a data class. Or you keep the currency elsewhere: many payment services give each account one currency, so the amount needs none of its own.\n\nWhere do value classes pay off? IDs and keys (`PaymentId`, `MerchantId`, `IdempotencyKey`), amounts in minor units, and validated strings such as an IBAN: anywhere two `String`s or two `Long`s could be swapped by accident. Validation runs once, in `init`, and the type is the proof that it ran. Where don't they? In APIs that Java code calls a lot, unless you add `@JvmName` overloads or `@JvmExposeBoxed`, and in classes that reflection-heavy frameworks read. Keep them in the Kotlin domain code and convert at the edges.",
   "try": {
    "title": "Try a second field",
    "minutes": 2,
    "steps": [
     "In `ValueClassDemo.kt`, change `value class Cents(val value: Long)` to `value class Cents(val value: Long, val currency: String)`. Run the demo.",
     "Undo it. Which of your own types would you make a value class, and which would stay a data class?"
    ],
    "expect": "The build fails with `value class must have exactly one primary constructor parameter.` Single-value concepts such as ids, keys and minor-unit amounts fit. Anything with two parts (amount plus currency, a card's expiry month and year) stays a data class for now."
   }
  }
 ],
 "analogy": "A value class is a label the compiler checks and then peels off. Inside Kotlin, the label `Money` stops you from putting an order id in the amount slot. At run time the label is gone and only the number travels, except when the number has to go somewhere that only takes objects, like a list. Then the compiler packs it in a box with the label printed on the outside. The analogy breaks at the border with Java: Java can't read the label at all, so it either can't call the function, or, through `@JvmName`, hands in a bare number that nobody checked.",
 "in_your_world": "Payment code is full of values that share a JVM type and must never be mixed. `paymentId`, `merchantId` and `idempotencyKey` are all `String`; `amountMinor`, `feeMinor` and `createdAtEpochMs` are all `Long`. One value class per concept turns a swapped argument in `refund(merchantId, paymentId)` into a compile error, with no allocation in Kotlin code. Keep them in the domain and service layers of your Quarkus service. At the edges, look at what reads them: a REST DTO with `val amount: Money` has a getter named `getAmount-<hash>` in the bytecode, and the Java modules your team still maintains can't call a mangled function until you add `@JvmName` or `@JvmExposeBoxed`.",
 "mistake": "Believing a value class is never boxed, and then counting on it in a hot path that goes through generics. A `Map<PaymentId, Money>` or a `List<Money>` holds a boxed object per entry, exactly like `List<Long>`, and a nullable `Money?` field holds a reference to a box:\n\n```java\nList<Long> amounts = new ArrayList<>();\nfor (long m : rawAmounts) amounts.add(m);          // one Long object per element\n```\n\n```kotlin\nval amounts = ArrayList<Money>()\nfor (m in rawAmounts) amounts += Money(m)         // one Money object per element\n```\n\nThe value class still gives you type safety in those places, just not the allocation savings. Profile before you rely on them, and use a primitive array (`LongArray`) for large numeric batches.",
 "compare": {
  "title": "An idempotency key: Java record vs Kotlin value class",
  "java": {"title": "IdempotencyKey.java", "src": "public record IdempotencyKey(String value) {\n    public IdempotencyKey {\n        if (value.length() < 8 || value.length() > 64)\n            throw new IllegalArgumentException(\"idempotency key must be 8 to 64 characters\");\n        if (!value.matches(\"[A-Za-z0-9_-]+\"))\n            throw new IllegalArgumentException(\"bad character in idempotency key: \" + value);\n    }\n}\n\n// every new IdempotencyKey(...) is an object with identity\nstatic Charge findCharge(IdempotencyKey key) { ... }   // JVM: findCharge(IdempotencyKey)"},
  "kotlin": {"title": "IdempotencyKey.kt", "src": "@JvmInline\nvalue class IdempotencyKey(val value: String) {\n    init {\n        require(value.length in 8..64) { \"idempotency key must be 8 to 64 characters\" }\n        require(value.matches(Regex(\"[A-Za-z0-9_-]+\"))) { \"bad character in idempotency key: $value\" }\n    }\n}\n\n// IdempotencyKey(...) runs init and returns the same String\nfun findCharge(key: IdempotencyKey): Charge? = TODO()  // JVM: findCharge-<hash>(String)"},
  "note": "Both validate once at construction and both compare by value. The record is a real object: each `new` allocates, and a map keyed by it holds those objects. The value class is a `String` at run time wherever it is used as itself, so `findCharge` costs exactly what a `String` parameter costs. The price is on the Java side: Java sees `findCharge-<hash>(String)`, which it can't call, and can't construct an `IdempotencyKey` at all without `@JvmExposeBoxed`. JEP 401, a preview in JDK 28, adds `value record` to Java: a record without identity, which gives the JVM room to flatten it."
 },
 "worked": {
  "title": "Make a swapped argument a compile error, then give Java a safe door",
  "steps": [
   {"say": "A refund call takes two `String`s and a `Long`. Someone swapped the ids in a hotfix, and it compiled.",
    "code": "static String refund(String merchantId, String paymentId, long amountMinor) { ... }\n\nrefund(paymentId, merchantId, 1_999);   // swapped: compiles, refunds the wrong thing", "lang": "java",
    "alt_lang": "kotlin", "alt_code": "fun refund(merchantId: String, paymentId: String, amountMinor: Long): String = TODO()\n\nrefund(paymentId, merchantId, 1_999)    // swapped: compiles, refunds the wrong thing"},
   {"say": "Give each concept its own value class. The swapped call now fails to compile, twice, and nothing allocates: in the bytecode the function still takes two Strings and a long.",
    "code": "@JvmInline value class MerchantId(val value: String)\n@JvmInline value class PaymentId(val value: String)\n@JvmInline value class Money(val cents: Long)\n\n// 1. one type per concept\nfun refund(merchant: MerchantId, payment: PaymentId, amount: Money): String = TODO()\n\nrefund(payment, merchant, Money(1_999))\n// error: argument type mismatch: actual type is 'PaymentId', but 'MerchantId' was expected.\n// error: argument type mismatch: actual type is 'MerchantId', but 'PaymentId' was expected.", "lang": "kotlin",
    "alt_lang": "java", "alt_code": "// Java gets the same safety from records, at the cost of an object each\nrecord MerchantId(String value) {}\nrecord PaymentId(String value) {}\n\nstatic String refund(MerchantId merchant, PaymentId payment, long amountMinor) { ... }\n\nrefund(payment, merchant, 1_999);   // error: incompatible types: PaymentId cannot be converted to MerchantId"},
   {"say": "Check the Java view. `javap` shows `refund-<hash>(String, String, long)`: the Java module that also issues refunds can't call it any more. Don't reach for `@JvmName` here, because Java would pass raw values past every `init`. Add a Java entry point that takes the raw types and builds the value classes, so validation runs.",
    "code": "// 2. a door for Java: raw types in, value classes (and their init blocks) inside\nfun refundFromJava(merchantId: String, paymentId: String, amountMinor: Long): String =\n    refund(MerchantId(merchantId), PaymentId(paymentId), Money(amountMinor))\n\n// javap: refund-<hash>(String, String, long) and refundFromJava(String, String, long)", "lang": "kotlin",
    "alt_lang": "java", "alt_code": "// 3. the Java module calls the plain name; a negative amount fails inside Money's init\nString result = RefundsKt.refundFromJava(\"m-981\", \"pay_7\", 1_999L);"},
   {"say": "Java can still swap the two strings in `refundFromJava`, so the door is a compromise: it validates values, it can't check names. That's why the type safety belongs in Kotlin and the door belongs at the edge, used by as few callers as possible.", "code": "", "lang": ""}
  ]
 },
 "lab": {
  "title": "Money and IdempotencyKey value classes with validation",
  "minutes": 13,
  "files": [f"{lab}/main/{P}/Money.kt", f"{lab}/main/{P}/IdempotencyKey.kt", f"{lab}/main/{P}/Receipts.kt"],
  "run": "./gradlew :kotlin:test --tests 'workbench.kotlin.l02.*'",
  "steps": [
   "Run the tests. All nine fail.",
   "In `Money.kt`, add the `init` block (TODO 1), then write `plus`, `times`, `compareTo`, `toString` and `parse` (TODOs 2 to 5).",
   "In `IdempotencyKey.kt`, add the `init` block (TODO 6): 8 to 64 characters, ASCII letters, digits, `-` and `_` only.",
   "In `Receipts.kt`, write `receiptLine`, then add the Java entry point (TODO 7) with `@JvmName`. Make it validate.",
   "Run the tests until all nine pass. Then run `javap -p -cp kotlin/build/classes/kotlin/main workbench.kotlin.l02.ReceiptsKt` and match each name to the Kotlin function it came from."
  ],
  "hints": [
   "`init { require(cents >= 0) { \"amount must be non-negative, was $cents\" } }` goes inside the class body.",
   "`BigDecimal(\"1.234\").setScale(2)` throws `ArithmeticException: Rounding necessary`. That's what you want, so don't pass a rounding mode.",
   "For ASCII only, test `it in 'a'..'z' || it in 'A'..'Z' || it in '0'..'9' || it == '-' || it == '_'`. `isLetterOrDigit()` alone also accepts letters such as `é`.",
   "TODO 7: `@JvmName(\"receiptLineForJava\") fun receiptLineJava(amount: Money): String = receiptLine(Money(amount.cents))`. Building a new `Money` calls `constructor-impl`, which runs `init`.",
   "Keep `override fun toString(): String` with its explicit return type. Kotlin 2.4.21 (and 2.3.21) crash with `Backend Internal error: Exception during IR lowering` when a value class's `toString()` infers its type from a Java call such as `toPlainString()` and the value is then used in a string template."
  ],
  "done_when": "All nine tests in `MoneyTest` and `ReceiptsFromJavaTest` pass."
 },
 "drill": {
  "title": "Write a validated Iban from memory",
  "minutes": 4,
  "prompt": "Close this page. Write `@JvmInline value class Iban(val value: String)` that rejects anything other than 15 to 34 characters of capital letters and digits starting with two letters. Then write the Java record version. Which one allocates when you call `send(to: Iban)` with it, and what is the JVM name of `send` in each language?",
  "answer": {"lang": "kotlin", "src": "@JvmInline\nvalue class Iban(val value: String) {\n    init {\n        require(value.length in 15..34) { \"IBAN must be 15 to 34 characters\" }\n        require(value.matches(Regex(\"[A-Z]{2}[A-Z0-9]+\"))) { \"bad IBAN: $value\" }\n    }\n}\n\nfun send(to: Iban): Unit = TODO()   // JVM: send-<hash>(String); no object is created",
             "alt": {"lang": "java", "title": "Iban.java", "src": "public record Iban(String value) {\n    public Iban {\n        if (value.length() < 15 || value.length() > 34)\n            throw new IllegalArgumentException(\"IBAN must be 15 to 34 characters\");\n        if (!value.matches(\"[A-Z]{2}[A-Z0-9]+\"))\n            throw new IllegalArgumentException(\"bad IBAN: \" + value);\n    }\n}\n\nstatic void send(Iban to) { }   // JVM: send(Iban); every new Iban(...) is an object"}}
 },
 "recap": [
  "`@JvmInline value class X(val v: T)` has one property, validates in `init`, is its own type in Kotlin and a plain `T` in the bytecode wherever it's used as itself.",
  "It is boxed whenever it's used as another type: a generic `T`, a nullable `X?`, an interface, `Any`, and so every collection.",
  "Functions that take a value class get mangled JVM names such as `charge-X49TzF8(long)`. That avoids overload clashes and keeps Java out.",
  "`@JvmName` lets Java call such a function, but Java passes the raw value and skips `init`, so validate again. `@JvmExposeBoxed` (Experimental, opt-in) gives Java a constructor that runs `init`.",
  "A type alias is only a second name. A value class is a new type.",
  "Only one field on the JVM. Multi-field value classes wait for Valhalla, and JEP 401 is a preview in JDK 28."
 ],
 "quiz": [
  {"q": "`@JvmInline value class Money(val cents: Long)`. Which call boxes `m`?",
   "options": ["`total(m, other)`, where `fun total(a: Money, b: Money) = a + b`", "`audit(m)`, where `fun audit(x: Any?)`", "`Invoice(amount = m)`, where `class Invoice(val amount: Money)`", "`m.cents * 2`"],
   "answer": 1, "why": "`Any?` is another type, so the compiler calls `Money.box-impl` before `audit`. `total` takes `Money` as itself (two longs in the bytecode), `Invoice` stores a `long` field, and `m.cents` reads the long directly."},
  {"q": "What can Java call for `fun refund(id: PaymentId, amount: Money): Boolean`, where both are value classes over `String` and `Long`?",
   "options": ["`refund(PaymentId, Money)`", "`refund(String, long)`", "Nothing: value classes can't be parameters of top-level functions", "Nothing by that name: the JVM method is `refund-<hash>(String, long)`, which javac can't call"],
   "answer": 3, "why": "Functions with value-class parameters are mangled, and the `-` makes the name impossible to write in Java. The parameters are the underlying types, so it isn't `refund(PaymentId, Money)` either. Add `@JvmName`, a raw-typed entry point, or `@JvmExposeBoxed` for Java."},
  {"q": "Java calls `ReceiptsKt.receiptLineForJava(-500L)`. In Kotlin: `@JvmName(\"receiptLineForJava\") fun receiptLineJava(amount: Money) = \"EUR $amount\"`, and `Money`'s `init` rejects negative amounts. What happens?",
   "options": ["It returns `\"EUR -5.00\"`: Java passed a raw long, so no `Money` was constructed and `init` never ran", "`IllegalArgumentException` from Money's `init`", "javac refuses the call, because the parameter is a `Money`", "`ClassCastException` at run time"],
   "answer": 0, "why": "`init` runs in `constructor-impl`, which only runs when someone writes `Money(...)`. Java skipped that and handed the function a bare `long`. The fix is to build a fresh `Money(amount.cents)` inside the Java entry point."},
  {"q": "You try `@JvmInline value class Price(val cents: Long, val currency: String)`. What does Kotlin 2.4 do?",
   "options": ["It compiles, and the JVM stores a long and a reference", "It compiles if you add `-XXLanguage:+ValueClasses`", "It reports `value class must have exactly one primary constructor parameter.`", "It compiles, but every use is boxed"],
   "answer": 2, "why": "On the JVM a value class has exactly one field. Even the internal flag `-XXLanguage:+ValueClasses` only earns `warning: unknown language feature 'ValueClasses'`, and the error stays. Multi-field value classes wait for Valhalla support in the JVM."},
  {"q": "From the last lesson: `inline fun <T> inTx(block: () -> T): T = runner.execute(Callable { block() })`. What does the compiler ask for?",
   "options": ["`noinline` on `block`", "`crossinline` on `block`, because it's called inside the `Callable`", "`reified` on `T`", "Nothing: it compiles as written"],
   "answer": 1, "why": "`block` runs inside the `Callable`, another execution context, so a non-local `return` in the caller's lambda couldn't work. The compiler says `it might contain non-local returns` and asks for `crossinline`.",
   "from": "kt-01"}
 ],
 "flashcards": [
  {"front": "What does `@JvmInline value class PaymentId(val value: String)` compile to where it's used as a `PaymentId`?", "back": "A plain `String`. `PaymentId(...)` calls the static `constructor-impl`, which runs `init` and returns the same String."},
  {"front": "When is a value class boxed?", "back": "Whenever it's used as another type: a generic `T`, a nullable `X?`, an interface it implements, or `Any` (collections, `println`)."},
  {"front": "Why does `fun charge(amount: Cents)` compile to `charge-X49TzF8(long)`?", "back": "Mangling. It avoids clashes with overloads on the underlying type, and Java can't call a name with a `-` in it."},
  {"front": "What does `@JvmName` on a value-class function give Java, and what's the catch?", "back": "A name Java can call. Java passes the raw underlying value, so `init` never runs: validate again inside."},
  {"front": "Type alias vs value class?", "back": "An alias is another name, assignment-compatible with the original type. A value class is a new type: a `Long` won't go where `Cents` is expected."},
  {"front": "How many properties can a Kotlin value class have on the JVM?", "back": "Exactly one: `value class must have exactly one primary constructor parameter.` More waits for Valhalla."},
  {"front": "What does `@JvmExposeBoxed` add, and what does it need?", "back": "A public constructor that runs `init`, and boxed overloads Java can call. It's Experimental: `@OptIn(ExperimentalStdlibApi::class)`."}
 ],
 "terms": [
  {"term": "Value class", "plain": "`@JvmInline value class X(val v: T)`: its own type in Kotlin, its single property `T` at run time where possible."},
  {"term": "Boxing", "plain": "Wrapping the underlying value in a real object of the value class, done when it is used as another type."},
  {"term": "Name mangling", "plain": "The hash suffix, as in `charge-X49TzF8`, that the compiler adds to functions with value-class parameters."},
  {"term": "@JvmName", "plain": "Sets the JVM name of a function, which can remove the mangled suffix so Java can call it."},
  {"term": "@JvmExposeBoxed", "plain": "Experimental annotation (Kotlin 2.2+) that adds Java-callable boxed constructors and overloads."},
  {"term": "Type alias", "plain": "A second name for an existing type. It adds no type safety."},
  {"term": "Project Valhalla", "plain": "The OpenJDK project that adds value objects without identity to the JVM. JEP 401 is a preview in JDK 28."}
 ],
 "explain_back": {
  "prompt": "A teammate who mostly writes Java asks why `fun charge(m: Money)` costs no allocation but `List<Money>` does, and why their Java code can't call `charge`. Explain both in your own words.",
  "answer": "A value class exists for the compiler, not for the JVM. Where the code uses a `Money` as a `Money` (a parameter, a field, a return value), the compiler passes the `long` inside it, so `charge` really takes a `long` and nothing is allocated. A `List` holds objects, so when a `Money` goes into one, the compiler has to wrap the long in a real `Money` object first, the same way Java wraps a `long` in a `Long`. That's boxing, and it happens whenever the value is used as another type: generic, nullable, interface or `Any`. Java can't call `charge` because the compiler mangles its name to something like `charge-X49TzF8(long)`. The hash avoids clashes with a `charge(Long)` overload and keeps unchecked longs out. To let Java in, add a function with `@JvmName`, or one that takes a raw `Long` and builds the `Money` itself, so the validation in `init` still runs."
 },
 "deeper": {
  "minutes": 8,
  "body": "Two details that matter when you design with value classes.\n\nA value class can wrap a generic type: `@JvmInline value class Box<T>(val value: T)`. The docs say the underlying type is then mapped to `Any?`, or to the upper bound of `T`, so at run time it's an `Object` field and you rarely save anything. Generic value classes help for type safety, not for speed.\n\nThe second detail is a compiler bug worth knowing about. In Kotlin 2.4.21 (and 2.3.21) this crashes the compiler with `Backend Internal error: Exception during IR lowering` and a `NoSuchElementException` from the string-concatenation lowering:\n\n```text\n@JvmInline value class M(val c: Long) { override fun toString() = java.math.BigDecimal.valueOf(c, 2).toPlainString() }\nfun f(m: M) = \"x $m\"\n```\n\nThe trigger is the inferred return type: `toPlainString()` returns a Java platform type, `String!`. Write `override fun toString(): String = ...` and it compiles. It's a small, concrete argument for explicit return types on anything public: they keep platform types from leaking into your API, and here they also keep the compiler alive.\n\nFinally, the history of the keyword, which explains old code you'll still meet. Kotlin 1.5.0 made these classes stable with the `value` modifier plus `@JvmInline` on the JVM, and deprecated the old `inline class` spelling with a warning. The design notes give the reason for the split: `@JvmInline` names today's erasure trick, which leaves the plain `value class` free to mean a real Valhalla value class one day."
 },
 "sources": [
  {"title": "Inline value classes (Kotlin docs)", "url": "https://kotlinlang.org/docs/inline-classes.html"},
  {"title": "Calling Kotlin from Java (Kotlin docs)", "url": "https://kotlinlang.org/docs/java-to-kotlin-interop.html"},
  {"title": "What's new in Kotlin 2.2.0 (@JvmExposeBoxed)", "url": "https://kotlinlang.org/docs/whatsnew22.html"},
  {"title": "KEEP design notes: value classes", "url": "https://github.com/Kotlin/KEEP/blob/master/notes/value-classes.md"},
  {"title": "JEP 401: value objects for the JVM (Project Valhalla, preview)", "url": "https://openjdk.org/jeps/401"}
 ]
}
out = ROOT / "content/lessons/kt-02.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
