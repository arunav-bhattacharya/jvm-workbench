# Kotlin functional collection operations and lazy sequences, compared with Java Streams

Scope: Kotlin 2.4.21 stdlib (the course version), JDK 21 to 25. Audience: experienced Java/Kotlin engineers new to functional style.

How these notes were checked:
- **Stdlib sources** were read at the `v2.4.21` tag of JetBrains/kotlin. Quotes from them are verbatim.
- **JDK Javadoc text** was read from OpenJDK sources on GitHub, because docs.oracle.com is blocked from this session. The Oracle package-summary page is generated from the same `package-info.java`.
- **Runtime behaviour, exception messages and bytecode** were checked locally:
  - Kotlin compiler `kotlin-compiler-embeddable-2.4.21` from `~/.gradle/caches`, `-jvm-target 21`
  - OpenJDK 21.0.12, `javap -c -p -v`
  - JMH 1.37
- **Tags:** findings checked that way are marked **[local]**.
- **Blocked hosts:** kt.academy, leanpub.com, codementor.io, discuss.kotlinlang.org and openjdk.org could not be reached. Effective Kotlin and Kotlin in Action passages could not be verified (see Gaps).

Local probe programs: `Demo.kt`, `Bytecode.kt`, `Extra.kt`, `sam/Sam.kt` and `bench/` are in the session scratchpad, `/tmp/claude-0/-home-user/b1ec521c-18dd-5b5d-967f-de5283ba1787/scratchpad/kc/` and `.../scratchpad/bench/`. The scratchpad is temporary. Every output a lesson needs is copied into these notes.

Shared example data used in the [local] outputs below:

```kotlin
enum class Status { SETTLED, PENDING, FAILED }
data class Payment(val id: Int, val merchant: String, val amountCents: Long, val status: Status, val refund: Long? = null)

val payments = listOf(
    Payment(1, "acme",    1_500,  Status.SETTLED),
    Payment(2, "globex",  9_900,  Status.PENDING),
    Payment(3, "acme",    2_000,  Status.SETTLED, refund = 500),
    Payment(4, "initech", 12_000, Status.FAILED),
    Payment(5, "globex",  700,    Status.SETTLED),
)
```

---

## 1. The core operations and what each one really does

### Takeaway
On `Iterable`, almost every operation is an `inline` function. It loops once over the receiver and writes into a brand-new `ArrayList` or `LinkedHashMap`, so each step in a chain produces a whole new collection.

The edge cases are where engineers get bitten:
- `reduce`, `first` and `maxOf` throw on an empty collection.
- `associateBy` silently keeps the last value on duplicate keys.
- `zip` truncates to the shorter input.
- `distinctBy` keeps the first element per key.
- `sortedBy` is stable.
- `groupingBy` aggregates in one pass with no per-group lists.

### Cited Findings

**Transformations**
- `map` "applies the given lambda function to each subsequent element and returns the list of the lambda results. The order of results is the same as the original order of elements." — [Kotlin docs: Collection transformations](https://kotlinlang.org/docs/collection-transformations.html)
- `map` source in 2.4.21 is `public inline fun <T, R> Iterable<T>.map(transform: (T) -> R): List<R>`, with body `mapTo(ArrayList<R>(collectionSizeOrDefault(10)), transform)`. The result list is pre-sized from the source size, or 10 if the size is unknown. — [stdlib _Collections.kt @v2.4.21](https://raw.githubusercontent.com/JetBrains/kotlin/v2.4.21/libraries/stdlib/common/src/generated/_Collections.kt)
- `filter` is `public inline fun <T> Iterable<T>.filter(predicate: (T) -> Boolean): List<T>`, with body `filterTo(ArrayList<T>(), predicate)`. It is not pre-sized, so the list grows as matches are added. — [_Collections.kt](https://raw.githubusercontent.com/JetBrains/kotlin/v2.4.21/libraries/stdlib/common/src/generated/_Collections.kt)
- `mapNotNull` is inline: `mapNotNullTo(ArrayList<R>(), transform)`. The docs say: "you can filter out the `null`s from the result collection by calling the `mapNotNull()` function instead of `map()`". — [_Collections.kt](https://raw.githubusercontent.com/JetBrains/kotlin/v2.4.21/libraries/stdlib/common/src/generated/_Collections.kt); [Collection transformations](https://kotlinlang.org/docs/collection-transformations.html)
- **[local]** `payments.mapNotNull { it.refund }` → `[500]`.
- `flatMap` has two inline overloads:
  - one where the lambda returns an `Iterable<R>`;
  - one where it returns a `Sequence<R>` (`@JvmName("flatMapSequence")`, since 1.4).

  The docs describe `flatMap()` as "a subsequent call of `map()` (with a collection as a mapping result) and `flatten()`". `flatten()` "returns a single `List` of all the elements of the nested collections." — [_Collections.kt](https://raw.githubusercontent.com/JetBrains/kotlin/v2.4.21/libraries/stdlib/common/src/generated/_Collections.kt); [Collection transformations](https://kotlinlang.org/docs/collection-transformations.html)
- **[local]** `listOf(listOf(1,2), listOf(3), emptyList()).flatten()` → `[1, 2, 3]`. `flatMap { b -> b.map { it * 10 } }` → `[10, 20, 30]`.

**Folding and reducing**
- reduce vs fold: "`fold()` takes an initial value and uses it as the accumulated value on the first step, whereas the first step of `reduce()` uses the first and the second elements as operation arguments on the first step." — [Kotlin docs: Aggregate operations](https://kotlinlang.org/docs/collection-aggregate.html)
- **Why `reduce` throws on empty.** `reduce` has no initial value, so on an empty receiver it has nothing to return. The source:

  ```kotlin
  public inline fun <S, T : S> Iterable<T>.reduce(operation: (acc: S, T) -> S): S {
      val iterator = this.iterator()
      if (!iterator.hasNext()) throw UnsupportedOperationException("Empty collection can't be reduced.")
      ...
  ```

  Its KDoc: "Throws an exception if this collection is empty. If the collection can be empty in an expected way, please use [reduceOrNull] instead."

  Note the signature. The accumulator type `S` must be a *supertype* of the element type `T`, while `fold`'s accumulator `R` can be anything. — [_Collections.kt](https://raw.githubusercontent.com/JetBrains/kotlin/v2.4.21/libraries/stdlib/common/src/generated/_Collections.kt)
- "All reduce operations throw an exception on empty collections. To receive `null` instead, use their `*OrNull()` counterparts": `reduceOrNull()`, `reduceRightOrNull()`, `reduceIndexedOrNull()` and `reduceRightIndexedOrNull()`. — [Aggregate operations](https://kotlinlang.org/docs/collection-aggregate.html)
- **[local] Empty-collection behaviour, `emptyList<Long>()`:**

  | Call | Result |
  |---|---|
  | `fold(0L){…}` | `0` |
  | `reduceOrNull{…}` | `null` |
  | `sum()` | `0` |
  | `reduce{…}` | `java.lang.UnsupportedOperationException: Empty collection can't be reduced.` |
  | `emptySequence<Long>().reduce{…}` | `UnsupportedOperationException: Empty sequence can't be reduced.` |
  | `first()` | `java.util.NoSuchElementException: List is empty.` |
  | `maxOf{it}` | `java.util.NoSuchElementException` (message `null`) |
  | `firstOrNull()` | `null` |
  | `maxOrNull()` | `null` |

  The Java contrast: `Stream.empty<Long>().reduce { a, b -> a + b }` returns `Optional.empty`.
- `runningFold()` "(or its synonym `scan()`)" and `runningReduce()` save the intermediate accumulator values. — [Aggregate operations](https://kotlinlang.org/docs/collection-aggregate.html)
- `runningFold` and `scan` are both `public inline fun <T, R> Iterable<T>.…(initial: R, operation: (acc: R, T) -> R): List<R>`. — [_Collections.kt](https://raw.githubusercontent.com/JetBrains/kotlin/v2.4.21/libraries/stdlib/common/src/generated/_Collections.kt)
- **[local]** Running totals over amounts `[1500, 9900, 2000, 12000, 700]`:
  - `runningFold(0L)` → `[0, 1500, 11400, 13400, 25400, 26100]`. The result has n+1 elements and includes the initial value.
  - `scan(0L)` → the identical list.
  - `runningReduce` → `[1500, 11400, 13400, 25400, 26100]`, n elements.
- `foldRight`/`reduceRight` start from the last element. "When folding or reducing right, the operation arguments change their order: first goes the element, and then the accumulated value." — [Aggregate operations](https://kotlinlang.org/docs/collection-aggregate.html)

**Sums, counts and min/max**
- `sumOf` "takes a selector function and returns the sum of its application to all collection elements". — [Aggregate operations](https://kotlinlang.org/docs/collection-aggregate.html)
- `sumOf` overloads in 2.4.21 common stdlib take selectors returning `Double`, `Int`, `Long`, `UInt` or `ULong`. They are inline, use JvmNames `sumOfDouble`, `sumOfInt` and so on, and use `@OverloadResolutionByLambdaReturnType`. — [_Collections.kt](https://raw.githubusercontent.com/JetBrains/kotlin/v2.4.21/libraries/stdlib/common/src/generated/_Collections.kt)
- **[local]** A `BigDecimal` overload also exists on the JVM: `payments.sumOf { BigDecimal(it.amountCents).movePointLeft(2) }` → `261.00`. `sumOf { it.amountCents }` → `26100` (Long).
- `minOrNull()`/`maxOrNull()` "On empty collections, they return `null`". `maxOf`/`minOf`/`maxOfWith`/`minOfWith` "do the same as their counterparts but throw a `NoSuchElementException` on empty collections." — [Aggregate operations](https://kotlinlang.org/docs/collection-aggregate.html)
- `maxByOrNull` is inline (since 1.4):
  - it returns `null` for an empty collection;
  - for a single element, it returns that element without calling the selector;
  - on ties, the first element wins.

  — [_Collections.kt](https://raw.githubusercontent.com/JetBrains/kotlin/v2.4.21/libraries/stdlib/common/src/generated/_Collections.kt)
- **[local]** `payments.maxByOrNull { it.amountCents }?.id` → `4`.
- `count()` overloads:
  - `Iterable<T>.count()` is not inline and iterates;
  - `Collection<T>.count()` is `@InlineOnly` and returns `size`;
  - `count(predicate)` is inline.

  — [_Collections.kt](https://raw.githubusercontent.com/JetBrains/kotlin/v2.4.21/libraries/stdlib/common/src/generated/_Collections.kt)
- **[local]** `payments.count { it.status == Status.SETTLED }` → `3`.

**Grouping**
- `groupBy()` "returns a `Map`. In this map, each key is the lambda result, and the corresponding value is the `List` of elements on which this result is returned." It has an optional second `valueTransform` lambda. — [Kotlin docs: Grouping](https://kotlinlang.org/docs/collection-grouping.html)
- `groupBy` KDoc: "The returned map preserves the entry iteration order of the keys produced from the original collection." — [_Collections.kt](https://raw.githubusercontent.com/JetBrains/kotlin/v2.4.21/libraries/stdlib/common/src/generated/_Collections.kt)
- **[local]** Results on `payments`:
  - `groupBy({ it.merchant }, { it.id })` → `{acme=[1, 3], globex=[2, 5], initech=[4]}`, runtime class `java.util.LinkedHashMap`.
  - `groupBy { it.status }.mapValues { (_, ps) -> ps.sumOf { it.amountCents } }` → `{SETTLED=4200, PENDING=9900, FAILED=12000}`.
- `groupingBy()` returns a `Grouping`. It "lets you apply operations to all groups in a lazy manner: the groups are actually built right before the operation execution." Its operations are `eachCount()`, `fold()`, `reduce()` and `aggregate()`. `aggregate()` "is the generic way to perform any operations on a `Grouping`." — [Grouping](https://kotlinlang.org/docs/collection-grouping.html)
- `Grouping.aggregateTo` makes one pass over the source and keeps one accumulator per key in the destination map. No per-group `List` is built:

  ```kotlin
  for (e in this.sourceIterator()) {
      val key = keyOf(e)
      val accumulator = destination[key]
      destination[key] = operation(key, accumulator, e, accumulator == null && !destination.containsKey(key))
  }
  ```

  — [stdlib Grouping.kt @v2.4.21](https://raw.githubusercontent.com/JetBrains/kotlin/v2.4.21/libraries/stdlib/src/kotlin/collections/Grouping.kt)
- On the JVM, `eachCount()` is implemented as `fold(0) { acc, e -> acc + 1 } optimized for boxing`. It uses mutable `kotlin.jvm.internal.Ref.IntRef` accumulators and then unwraps them with `mapValuesInPlace`. — [stdlib GroupingJVM.kt @v2.4.21](https://raw.githubusercontent.com/JetBrains/kotlin/v2.4.21/libraries/stdlib/jvm/src/kotlin/collections/GroupingJVM.kt)
- **[local]** Grouping results:
  - `groupingBy { it.merchant }.eachCount()` → `{acme=2, globex=2, initech=1}`.
  - `groupingBy { it.merchant }.fold(0L) { acc, p -> acc + p.amountCents }` → `{acme=3500, globex=10600, initech=12000}`.

**Associate and partition**
- `associate*` and duplicate keys:
  - `associateWith`: "If two elements are equal, only the last one remains in the map."
  - `associateBy`: "If two elements' keys are equal, only the last one remains in the map."
  - `associate()` "produces short-living `Pair` objects which may affect the performance. Thus, `associate()` should be used when the performance isn't critical or it's more preferable than other options."

  — [Collection transformations](https://kotlinlang.org/docs/collection-transformations.html)
- The `associate*` KDoc says: "If any two elements would have the same key returned by [keySelector] the last one gets added to the map. The returned map preserves the entry iteration order of the original collection." The implementations pre-size the map with `mapCapacity(collectionSizeOrDefault(10)).coerceAtLeast(16)`. — [_Collections.kt](https://raw.githubusercontent.com/JetBrains/kotlin/v2.4.21/libraries/stdlib/common/src/generated/_Collections.kt)
- **[local]** Results on `payments`:
  - `associateBy({ it.merchant }, { it.id })` → `{acme=3, globex=5, initech=4}`. Payment 1 is silently overwritten by 3, and 2 by 5.
  - The Java equivalent `Collectors.toMap(...)` throws `java.lang.IllegalStateException: Duplicate key acme (attempted merging values 1 and 3)`.
- `partition` is `public inline fun <T> Iterable<T>.partition(predicate: (T) -> Boolean): Pair<List<T>, List<T>>`. — [_Collections.kt](https://raw.githubusercontent.com/JetBrains/kotlin/v2.4.21/libraries/stdlib/common/src/generated/_Collections.kt)
- **[local]** `val (ok, notOk) = payments.partition { it.status == Status.SETTLED }` gives `[1, 3, 5] / [2, 4]`.

**Zip, chunked and windowed**
- `zip`: "If the collections have different sizes, the result of the `zip()` is the smaller size; the last elements of the larger collection are not included in the result." — [Collection transformations](https://kotlinlang.org/docs/collection-transformations.html)
- The `zip` KDoc says: "The returned list has length of the shortest collection." — [_Collections.kt](https://raw.githubusercontent.com/JetBrains/kotlin/v2.4.21/libraries/stdlib/common/src/generated/_Collections.kt)
- **[local]** `listOf(1,2,3).zip(listOf("a","b"))` → `[(1, a), (2, b)]`. `listOf(100,120,90).zipWithNext { a, b -> b - a }` → `[20, -30]`.
- `chunked`: "The last chunk may have a smaller size." When it is called with a transform, "the chunks are short-living `List`s that should be consumed right in that lambda." — [Kotlin docs: Retrieve collection parts](https://kotlinlang.org/docs/collection-parts.html)
- `windowed`:
  - `step` "defines a distance between first elements of two adjacent windows";
  - `partialWindows` "includes windows of smaller sizes that start from the elements at the end of the collection."

  `zipWithNext()` "creates a `Pair` for each element except the last one". — [Retrieve collection parts](https://kotlinlang.org/docs/collection-parts.html)
- `chunked` and `windowed` on `Iterable` are **not** inline (`public fun`); their transform overloads take a non-inline lambda. — [_Collections.kt](https://raw.githubusercontent.com/JetBrains/kotlin/v2.4.21/libraries/stdlib/common/src/generated/_Collections.kt)
- **[local]** On ids `[1..5]`:
  - `chunked(2)` → `[[1, 2], [3, 4], [5]]`
  - `windowed(3)` → `[[1, 2, 3], [2, 3, 4], [3, 4, 5]]`
  - `windowed(3, 2, partialWindows = true)` → `[[1, 2, 3], [3, 4, 5], [5]]`

**distinctBy and sorting**
- `distinctBy` KDoc: "Among elements of the given collection with equal keys, only the first one will be present in the resulting list. The elements in the resulting list are in the same order as they were in the source collection." It is inline and tracks keys in a `HashSet`. — [_Collections.kt](https://raw.githubusercontent.com/JetBrains/kotlin/v2.4.21/libraries/stdlib/common/src/generated/_Collections.kt)
- **[local]** `payments.distinctBy { it.merchant }.map { it.id }` → `[1, 2, 4]`.
- `sortedBy` is `public inline fun <T, R : Comparable<R>> Iterable<T>.sortedBy(crossinline selector: (T) -> R?): List<T>`, with body `sortedWith(compareBy(selector))`. Its KDoc says "The sort is _stable_. It means that elements for which [selector] returned equal values preserve their order". — [_Collections.kt](https://raw.githubusercontent.com/JetBrains/kotlin/v2.4.21/libraries/stdlib/common/src/generated/_Collections.kt)
- **[local]** Sorting results:
  - `sortedBy { it.amountCents }` → ids `[5, 1, 3, 2, 4]`.
  - `sortedWith(compareBy<Payment> { it.merchant }.thenByDescending { it.amountCents })` → `[3, 1, 2, 5, 4]`.

**first, any/all/none and take/drop**
- `first()` on a `List` returns element 0. Otherwise it iterates and throws `NoSuchElementException` (message "Collection is empty."). **[local]** On a `List` the message is "List is empty."
- `firstOrNull()` returns `null` instead of throwing.
- The predicate overloads `first {}`, `firstOrNull {}`, `any {}`, `all {}`, `none {}` and `count {}` are inline and stop at the first decisive element.
- `all` returns `true` for an empty collection.

  — [_Collections.kt](https://raw.githubusercontent.com/JetBrains/kotlin/v2.4.21/libraries/stdlib/common/src/generated/_Collections.kt)
- **[local]** On an empty list: `any()` → `false`, `all { it > 0 }` → `true`, `none()` → `true`.
- take, drop and their predicate forms:
  - `take()` and `takeLast()` return the whole collection "When called with a number larger than the collection size".
  - `takeWhile()` "takes the elements up to but excluding the first one not matching the predicate".
  - `dropWhile()` "returns the elements from the first one not matching the predicate to the end."

  — [Retrieve collection parts](https://kotlinlang.org/docs/collection-parts.html)
- **[local]** `listOf(1,2,5,1).takeWhile { it < 3 }` → `[1, 2]`. `dropWhile { it < 3 }` → `[5, 1]`. The trailing `1` is kept, which surprises people who expect filter-like behaviour.

**buildList and result types**
- **[local]** `buildList { add("header"); …; add("footer") }`:
  - returns runtime class `kotlin.collections.builders.ListBuilder`;
  - `(result as MutableList).add(…)` throws `UnsupportedOperationException`, so it really is sealed after building.
- **[local] Contrast:** `listOf(1,2).map { it }` is a `java.util.ArrayList`, and the cast-and-add succeeds. `listOf(1, 2)` is a `java.util.Arrays$ArrayList`, where `add` throws `UnsupportedOperationException`.

### Inferences
- Kotlin's direct functions cover most of what Java does with `collect(Collectors.…)`:
  - `groupBy`, `groupingBy{}.eachCount()` and `groupingBy{}.fold()`
  - `associateBy`, `partition`
  - `sumOf`, `maxByOrNull`
- **The rule of thumb to teach:** prefer `fold` (or `sumOf`, `count`, `maxByOrNull`) when the input can be empty. Use `reduce` only when "empty" is a programming error you want to surface loudly.
- For money, `sumOf { it.amountCents }` on a `Long` field gives a `Long`, and a `BigDecimal` selector picks the `BigDecimal` overload.
  - An `Int` selector gives an `Int` result. Totals above `Int.MAX_VALUE` cents (about $21.4M) would silently overflow, as normal JVM `Int` arithmetic does.
  - This is an inference from the overload set, not a separately tested case.
- `associateBy`'s silent last-wins is the most dangerous difference from Java (`toMap` throws). It matters for payments keyed by idempotency key or external id. Check for duplicates first with `groupingBy { key }.eachCount().filterValues { it > 1 }`.

### Gaps
- I did not locate the KDoc text of the JVM-only `sumOf` BigDecimal/BigInteger overloads (file `_CollectionsJvm.kt`). Its existence is verified only by compiling and running.
- `eachCountTo` and `aggregate` examples are not on the grouping docs page. They exist in Grouping.kt, but I did not quote them.

---

## 2. Eager Iterable vs lazy Sequence

### Takeaway
A chain on a `List` runs **horizontally**: each step processes the whole collection and materialises a new list before the next step starts. A `Sequence` chain runs **vertically**: nothing happens until a terminal operation, then each element travels through all steps before the next element is pulled. So `take`, `first` and `any` can stop early.

Two costs come with this:
- Stateful steps such as `sorted()` must buffer everything.
- Every intermediate step is a wrapper object holding a lambda.

In the local measurement, the biggest wins were these:
1. Short-circuiting: a Sequence was about 30,000× faster than the eager List chain at 1M elements.
2. Avoided allocation: about 26.5 MB per call for the List chain vs about 0.2 KB for the Sequence.

But a fused single-pass `sumOf` beat both.

### Cited Findings

**How the two models are defined**
- "Unlike collections, sequences don't contain elements, they produce them while iterating." — [Kotlin docs: Sequences](https://kotlinlang.org/docs/sequences.html)
- Eager vs lazy:
  - "When the processing of an `Iterable` includes multiple steps, they are executed eagerly: each processing step completes and returns its result – an intermediate collection."
  - Sequences are "executed lazily when possible: actual computing happens only when the result of the whole processing chain is requested."
  - "`Sequence` performs all the processing steps one-by-one for every single element. In turn, `Iterable` completes each step for the whole collection and then proceeds to the next step."

  — [Sequences](https://kotlinlang.org/docs/sequences.html)
- Official trade-off statement: sequences "let you avoid building results of intermediate steps, therefore improving the performance of the whole collection processing chain. However, the lazy nature of sequences adds some overhead which may be significant when processing smaller collections or doing simpler computations. Hence, you should consider both `Sequence` and `Iterable` and decide which one is better for your case." — [Sequences](https://kotlinlang.org/docs/sequences.html)
- Classification:
  - Stateless operations "require no state and process each element independently, for example, `map()` or `filter()`"; `take()`/`drop()` need a small constant amount.
  - Stateful operations "require a significant amount of state, usually proportional to the number of elements".
  - Intermediate operations return another lazily produced sequence. Terminal operations (e.g. `toList()`, `sum()`) are the only way to retrieve elements.

  — [Sequences](https://kotlinlang.org/docs/sequences.html)

**[local] Horizontal (List) vs vertical (Sequence) order**

Pipeline: `filter { SETTLED }.map { amountCents }.take(2)` over `payments`.

| List chain prints | Sequence chain prints |
|---|---|
| filter 1 | *(nothing until `toList()`; the chain is `kotlin.sequences.TakeSequence@…`)* |
| filter 2 | filter 1 |
| filter 3 | map 1 |
| filter 4 | filter 2 |
| filter 5 | filter 3 |
| map 1 | map 3 |
| map 3 | *(stops: payments 4 and 5 are never examined)* |
| map 5 | |
| result `[1500, 2000]` | result `[1500, 2000]` |

The official docs' version of this demo uses words: filter length > 3, map to length, take 4, over "The quick brown fox jumps over the lazy dog". The list version runs 9 filter calls and 5 map calls. The sequence version runs 6 filter calls and 4 map calls and never looks at "the", "lazy" or "dog". — [Sequences](https://kotlinlang.org/docs/sequences.html)

**What happens underneath**
- Intermediate Sequence operations are plain (non-inline) functions that return wrapper objects:
  - `map` → `TransformingSequence(this, transform)`
  - `filter` → `FilteringSequence(this, true, predicate)`
  - `mapNotNull` → `TransformingSequence(...).filterNotNull()`
  - `flatMap` → `FlatteningSequence`
  - `take` → `TakeSequence` (or `emptySequence()` for 0)
  - `distinctBy` → `DistinctSequence`

  `map` and `filter` are documented as "_intermediate_ and _stateless_"; `distinctBy` and `sorted` as "_intermediate_ and _stateful_". — [stdlib _Sequences.kt @v2.4.21](https://raw.githubusercontent.com/JetBrains/kotlin/v2.4.21/libraries/stdlib/common/src/generated/_Sequences.kt)
- `TransformingSequence` is just an iterator decorator that calls the stored lambda on each `next()`:

  ```kotlin
  internal class TransformingSequence<T, R>
  constructor(private val sequence: Sequence<T>, private val transformer: (T) -> R) : Sequence<R> {
      override fun iterator(): Iterator<R> = object : Iterator<R> {
          val iterator = sequence.iterator()
          override fun next(): R { return transformer(iterator.next()) }
          override fun hasNext(): Boolean { return iterator.hasNext() }
      }
  ```

  — [stdlib Sequences.kt @v2.4.21](https://raw.githubusercontent.com/JetBrains/kotlin/v2.4.21/libraries/stdlib/src/kotlin/collections/Sequences.kt)

**Why `sorted()` forces the whole upstream**
- `Sequence.sorted()` is `public fun` ("_intermediate_ and _stateful_"). When iterated, it does `val sortedList = this@sorted.toMutableList(); sortedList.sort()` and returns that list's iterator. So the first element requested pulls the entire upstream into memory. — [_Sequences.kt](https://raw.githubusercontent.com/JetBrains/kotlin/v2.4.21/libraries/stdlib/common/src/generated/_Sequences.kt)
- **[local]** `payments.asSequence().onEach { println("saw ${it.id}") }.sortedBy { it.amountCents }.first()` prints `saw 1` … `saw 5`, all five, before returning payment 5.

**Terminal operations are inline**
- Sequence terminal operations that only loop are inline: `fold`, `reduce`, `forEach`, `sumOf`, `count(predicate)`, `first(predicate)`, `groupBy` and `partition`. They return plain values or Lists/Maps. — [_Sequences.kt](https://raw.githubusercontent.com/JetBrains/kotlin/v2.4.21/libraries/stdlib/common/src/generated/_Sequences.kt)

**Building sequences and reusing them**
- Builders:
  - `sequenceOf(...)`
  - `asSequence()` on an `Iterable`
  - `generateSequence(seed) { next }`: "The sequence generation stops when the provided function returns `null`", otherwise it is infinite
  - `sequence { yield(x); yieldAll(iterable/iterator/sequence) }`

  On `yieldAll`: "A `Sequence` argument of `yieldAll()` can be infinite. However, such a call must be the last: all subsequent calls will never be executed." — [Sequences](https://kotlinlang.org/docs/sequences.html)
- `sequence {}` is `public fun <T> sequence(@BuilderInference block: suspend SequenceScope<T>.() -> Unit): Sequence<T> = Sequence { iterator(block) }`, since 1.3. The block is a restricted suspend lambda: each `yield` suspends it until the consumer asks for the next element. — [stdlib SequenceBuilder.kt @v2.4.21](https://raw.githubusercontent.com/JetBrains/kotlin/v2.4.21/libraries/stdlib/src/kotlin/collections/SequenceBuilder.kt)
- Reuse: "sequences can be iterated multiple times, but some sequence implementations might constrain themselves to be iterated only once." — [Sequences](https://kotlinlang.org/docs/sequences.html). The constrained ones are documented in the source:
  - `generateSequence(nextFunction)` without a seed: "The returned sequence is constrained to be iterated only once."
  - `Iterator<T>.asSequence()`: "The sequence is constrained to be iterated only once", implemented as `Sequence { this }.constrainOnce()`.

  — [Sequences.kt](https://raw.githubusercontent.com/JetBrains/kotlin/v2.4.21/libraries/stdlib/src/kotlin/collections/Sequences.kt)
- **[local] Reuse behaviour:**
  - `payments.asSequence().map { it.id }` iterated twice gives `[1..5]` both times. The whole pipeline re-runs, so any side effects happen twice.
  - A seedless `generateSequence { … }` or `iterator().asSequence()`, iterated a second time, throws `java.lang.IllegalStateException: This sequence can be consumed only once.`
- **[local] Builder demos:**
  - `generateSequence(100L) { (it * 2).takeIf { d -> d <= 1_600 } }` → `[100, 200, 400, 800, 1600]`. This is a retry-backoff schedule.
  - A Fibonacci `sequence { while (true) yield(...) }.take(10)` → `[0, 1, 1, 2, 3, 5, 8, 13, 21, 34]`.
  - A paged fetch, `sequence { for (page in 1..3) { println("fetching page $page"); yieldAll(...) } }.first { it > 15 }`, prints only "fetching page 1" and "fetching page 2". Page 3 is never fetched.

**[local] JMH measurement (own run; read the conditions)**

Setup:
- Kotlin 2.4.21 workloads (`-jvm-target 21`) called from a JMH 1.37 harness.
- OpenJDK 21.0.12 (C2), `-Xms1g -Xmx1g`.
- 1 fork, 3×1 s warmup, 3×1 s measurement, `Mode.AverageTime`, `-prof gc`.
- 4-vCPU Intel Xeon @ 2.10 GHz VM. **Load average was 17–19 during the run** because other workloads were sharing the host.

How to read the results:
- **Timing error bars are often larger than the means**, so treat times as order-of-magnitude only.
- **`gc.alloc.rate.norm` (bytes per operation) is deterministic and tight**, so it is the robust result.

Data: `Pay(id, amountCents, status)`. 60% of rows are SETTLED, and amounts are 1..100,000 cents. All variants returned identical answers.

*Full pass — total settled cents.* Values are time per call, with bytes allocated per call in brackets.

| Variant | n=10 | n=10,000 | n=1,000,000 |
|---|---|---|---|
| `for` loop | 21 ns (≈0 B) | 24 µs (≈0 B) | 5.2 ms (≈0 B) |
| `filter{}.map{}.sum()` on List | 156 ns (216 B) | 186 µs (243,041 B) | 148 ms (**26,507,194 B**) |
| `sumOf { if (settled) amount else 0L }` | 26 ns (≈0 B) | 12 µs (≈0 B) | 2.6 ms (≈0 B) |
| `asSequence().filter{}.map{}.sum()` | 39 ns (≈0 B) | 85 µs (105 B) | 9.0 ms (189 B) |
| `stream().filter{}.mapToLong{}.sum()` | 116 ns (368 B) | 15 µs (312 B) | 8.9 ms (428 B) |
| `stream().filter{}.map{}.reduce(0L){…}` (boxed) | 308 ns (552 B) | 153 µs (288,049 B) | 14 ms (**28,782,178 B**) |

*Short-circuit — id of the first settled payment above 99,000 cents.* The first match is at index 101; for n=10 there is no match, so every element is scanned.

| Variant | n=10 | n=10,000 | n=1,000,000 |
|---|---|---|---|
| List `filter{}.map{}.firstOrNull()` | 28 ns (≈0 B) | 25 µs (2,616 B) | 4.4 ms (243,286 B) |
| Sequence `filter{}.map{}.firstOrNull()` | 21 ns (≈0 B) | **131 ns** (≈0 B) | **141 ns** (≈0 B) |
| Stream `filter{}.map{}.findFirst()` | 157 ns (304 B) | 741 ns (320 B) | 981 ns (320 B) |

Raw iterations, e.g. seqFirst@1M `132, 142, 150 ns` and listFirst@1M `6.28, 4.03, 2.88 ms`, confirm that the short-circuit gap is real despite the noise. Results file: `scratchpad/bench/results.txt`.

### Inferences
- **Allocation is the cleanest teaching signal.**
  - The 2-step eager chain allocates about 26.5 MB per call at 1M elements: two `ArrayList`s plus about 600k boxed `Long`s.
  - The Sequence allocates about 0.2 KB, because C2 escape analysis scalar-replaced the boxes and wrappers in this simple, monomorphic benchmark.
  - Do not promise that elimination in general. It depends on inlining succeeding, and call sites shared by many lambdas in a real app become megamorphic.
- **"Sequences are slower for small collections" did not reproduce for this pipeline** (n=10: 39 ns vs 156 ns, with large error bars). The official docs say the overhead "may be" significant, which is a hedge, not a law. Teach "measure, and prefer fusing steps", not "sequences are slow when small".
- **The fastest idiomatic option was neither List chain nor Sequence: it was one fused inline call** (`sumOf` with the condition inside). That is effectively the hand-written loop. This makes a stronger lesson than "always `asSequence()`".
- **Laziness pays off hugely when the terminal operation can stop early**, as with `first`, `any` and `take` (four orders of magnitude at 1M here). For full passes it is a moderate win at large n and a wash at small n.
- **`sorted()` / `sortedBy()` in a sequence is a buffering barrier.** If you need the top-k, `sortedBy { }.take(k)` on a sequence still sorts everything; a bounded heap or `minByOrNull` (k=1) avoids that.

### Gaps
- No third-party JMH benchmark could be fetched and verified: Effective Kotlin's numbers are on blocked hosts, and the search results were snippets from blogs.
- The local run was on a heavily loaded VM. A lesson that quotes timings should re-run the JMH harness on a quiet machine with `-f 3 -i 5`. The allocation numbers can be quoted as-is.

---

## 3. Kotlin vs Java Streams

### Takeaway
A Java `Stream` is lazy and vertical like a Kotlin `Sequence`, with similar intermediate/terminal and stateless/stateful classifications. The practical differences:
- Streams are **single-use**.
- Streams can go **parallel**.
- Streams have **primitive specialisations** (`IntStream`, `LongStream`, `DoubleStream`).
- Streams finish through **`collect(Collectors…)`**, and `toMap` throws on duplicate keys.
- Kotlin sequences are **usually reusable** (they recompute), have **no parallel mode** and **no primitive specialisations**, and expose direct terminal functions that mirror the `Iterable` API.

Interop is one call each way (`asSequence()` / `asStream()`). On JDK 16+, `stream.toList()` in Kotlin resolves to the JDK member, which returns an unmodifiable list.

### Cited Findings

**How the Stream package defines itself**
- The `java.util.stream` package doc lists what makes a stream different from a collection:
  - "No storage."
  - "Functional in nature."
  - "Laziness-seeking. Many stream operations, such as filtering, mapping, or duplicate removal, can be implemented lazily … Intermediate operations are always lazy."
  - "Possibly unbounded … Short-circuiting operations such as `limit(n)` or `findFirst()` can allow computations on infinite streams to complete in finite time."
  - "Consumable. The elements of a stream are only visited once during the life of a stream. Like an Iterator, a new stream must be generated to revisit the same elements of the source."

  — [OpenJDK 21 java/util/stream/package-info.java](https://raw.githubusercontent.com/openjdk/jdk21u/master/src/java.base/share/classes/java/util/stream/package-info.java)
- "Traversal of the pipeline source does not begin until the terminal operation of the pipeline is executed." Also: "After the terminal operation is performed, the stream pipeline is considered consumed, and can no longer be used". And "filtering, mapping, and summing can be fused into a single pass on the data, with minimal intermediate state." — [package-info.java](https://raw.githubusercontent.com/openjdk/jdk21u/master/src/java.base/share/classes/java/util/stream/package-info.java)
- Stateless vs stateful: "Stateful operations, such as `distinct` and `sorted`, may incorporate state from previously seen elements … one cannot produce any results from sorting a stream until one has seen all elements of the stream." — [package-info.java](https://raw.githubusercontent.com/openjdk/jdk21u/master/src/java.base/share/classes/java/util/stream/package-info.java)
- **[local] Java Stream order matches the Sequence (vertical) model.** `listOf(1..5).stream().filter{odd}.map{*10}.limit(2)` printed `filter 1, map 1, filter 2, filter 3, map 3` → `[10, 30]`. With `peek → sorted() → peek → findFirst()`, all three "before sort" lines print before the first "after sort" line, the same barrier behaviour as Kotlin.

**Single-use streams**
- "A stream should be operated on (invoking an intermediate or terminal stream operation) only once … A stream implementation may throw `IllegalStateException` if it detects that the stream is being reused." — [OpenJDK 21 Stream.java](https://raw.githubusercontent.com/openjdk/jdk21u/master/src/java.base/share/classes/java/util/stream/Stream.java)
- **[local]** A second `count()` on the same stream throws `java.lang.IllegalStateException: stream has already been operated upon or closed`. A Kotlin `list.asSequence()` can be iterated again; it re-runs the pipeline.

**Parallel streams and side effects**
- "The stream implementations in the JDK create serial streams unless parallelism is explicitly requested." `parallelStream()` or `.parallel()` switches modes, and "The most recent sequential or parallel mode setting applies to the execution of the entire stream pipeline." Except for explicitly nondeterministic operations like `findAny()`, parallel vs serial "should not change the result of the computation." — [package-info.java](https://raw.githubusercontent.com/openjdk/jdk21u/master/src/java.base/share/classes/java/util/stream/package-info.java)
- Side-effect ordering: "Even when a pipeline is constrained to produce a result that is consistent with the encounter order … no guarantees are made as to the order in which the mapper function is applied to individual elements, or in what thread any behavioral parameter is executed". The Javadoc's anti-pattern is `.forEach(s -> results.add(s)); // Unnecessary use of side-effects!` — "If executed in parallel, the non-thread-safety of `ArrayList` would cause incorrect results". The fix is `.toList()`. — [package-info.java](https://raw.githubusercontent.com/openjdk/jdk21u/master/src/java.base/share/classes/java/util/stream/package-info.java)
- **[local]** `(1..16).toList().parallelStream().map { seen.add(it); it * 2 }.toList()` gave a correctly ordered result, but the order in `seen` ≠ encounter order on that run (expected; nondeterministic).
- Kotlin sequences have no parallel mode. The 2.4.21 `_Sequences.kt` contains no occurrence of "parallel" at all. — [_Sequences.kt](https://raw.githubusercontent.com/JetBrains/kotlin/v2.4.21/libraries/stdlib/common/src/generated/_Sequences.kt). Sequences live in the **common** stdlib source set (`libraries/stdlib/common/...`), so they are available on every Kotlin target. Java streams are JVM-only.

**Collectors vs Kotlin's direct functions**
- The official Java-to-Kotlin guide maps the Java idioms to Kotlin:

  | Java | Kotlin |
  |---|---|
  | `stream().filter(...)` | `filter {}` ("filtering is built into collections") |
  | `noneMatch` / `anyMatch` / `allMatch` | `none()` / `any()` / `all()` |
  | `Collectors.groupingBy(Request::getUrl)` | `groupBy(Request::url)` |
  | `groupingBy(classifier, counting())` | `eachCount()` |
  | `reduce()` | `reduce()`, `fold()` |
  | `distinct()` | `distinct()` |
  | `sorted()` | `sorted()` |

  For generated streams: Java `IntStream.iterate(1, e -> e + 3).limit(10).sum()` becomes Kotlin `generateSequence(1) { it + 3 }.take(10).sum()` (145). — [Kotlin docs: Collections in Java and Kotlin](https://kotlinlang.org/docs/java-to-kotlin-collections-guide.html)
- That guide does **not** say when to choose a Sequence over a Stream. — [Collections in Java and Kotlin](https://kotlinlang.org/docs/java-to-kotlin-collections-guide.html)
- Result-type guarantees differ:
  - `Collectors.toList()`: "There are no guarantees on the type, mutability, serializability, or thread-safety of the List returned".
  - `Collectors.groupingBy`: "There are no guarantees on the type, mutability, serializability, or thread-safety of the Map returned."
  - `Collectors.toMap`: "If the mapped keys contain duplicates … an `IllegalStateException` is thrown".

  — [OpenJDK 21 Collectors.java](https://raw.githubusercontent.com/openjdk/jdk21u/master/src/java.base/share/classes/java/util/stream/Collectors.java)
- **[local]** Results on JDK 21:
  - `Collectors.groupingBy(...)` returned a `java.util.HashMap` with keys in hash order (`{globex=2, acme=2, initech=1}`).
  - Kotlin `groupBy` returned a `LinkedHashMap` in first-seen key order (`{acme=…, globex=…, initech=…}`).
- `Stream.toList()` (since 16): "The returned List is unmodifiable; calls to any mutator method will always cause `UnsupportedOperationException` to be thrown." — [Stream.java](https://raw.githubusercontent.com/openjdk/jdk21u/master/src/java.base/share/classes/java/util/stream/Stream.java)

**Using Java streams from Kotlin**
- Kotlin interop functions in `kotlin.streams`, all since 1.2:
  - `Stream<T>.asSequence()`, `IntStream.asSequence()`, `LongStream.asSequence()`, `DoubleStream.asSequence()`;
  - `Sequence<T>.asStream()`: "Creates a sequential [Stream] instance that produces elements from the original sequence", implemented as `StreamSupport.stream({ Spliterators.spliteratorUnknownSize(iterator(), Spliterator.ORDERED) }, Spliterator.ORDERED, false)`;
  - `Stream<T>.toList(): List<T> = collect(Collectors.toList<T>())`, plus `IntStream`/`LongStream`/`DoubleStream.toList()` via `toArray().asList()`.

  — [stdlib jdk8 Streams.kt @v2.4.21](https://raw.githubusercontent.com/JetBrains/kotlin/v2.4.21/libraries/stdlib/jdk8/src/kotlin/streams/Streams.kt)
- **[local]** These compile with only `kotlin-stdlib-2.4.21.jar` on the classpath; no separate `-jdk8` artifact was needed.
  - `payments.asSequence().asStream().filter{…}.map{…}.toList()` → `[1, 3, 5]`, runtime class `java.util.ImmutableCollections$ListN`, and add throws `UnsupportedOperationException`.
  - `Bytecode.kt`'s `fun interopToList(s: Stream<Int>) = s.toList()` compiles to `invokeinterface java/util/stream/Stream.toList`. **The JDK 16 member wins over the Kotlin extension**, so the result is unmodifiable, not a Collectors.toList `ArrayList`.
  - `Stream.of(3,1,2).asSequence().sorted().toList()` → `[1, 2, 3]`.

**Primitive specialisations vs boxing**
- The stream package provides `IntStream`, `LongStream` and `DoubleStream`; the parallel example uses `.mapToInt(...).sum()`. — [package-info.java](https://raw.githubusercontent.com/openjdk/jdk21u/master/src/java.base/share/classes/java/util/stream/package-info.java)
- **[local]** In bytecode:
  - `mapToLong { it.amountCents }` takes a `ToLongFunction` whose LambdaMetafactory signature is `(Ljava/lang/Object;)J` (primitive long).
  - Kotlin's `Sequence.map { it.amountCents }` lambda is a `Function1` with instantiated type `(LP;)Ljava/lang/Long;` (boxed).
  - The eager List `map` calls `java/lang/Long.valueOf` per element.
- **[local] JMH:** boxed `stream().map{}.reduce(0L)` allocated about 28.8 MB per call at 1M, vs about 0.4 KB for `mapToLong{}.sum()`. Kotlin has no `LongSequence`; its primitive options are `LongArray`/`IntArray` (with `sum()`) or fusing into `sumOf`.

**JDK 24+ Gatherers fill Kotlin-only gaps**
- `java.util.stream.Gatherers` is `@since 24`: "Implementations of Gatherer that provide useful intermediate operations, such as windowing functions, folding functions, transforming elements concurrently, etc." Its built-ins are `windowFixed(int)`, `windowSliding(int)`, `fold(...)`, `scan(...)` and `mapConcurrent(...)`. — [OpenJDK 25 Gatherers.java](https://raw.githubusercontent.com/openjdk/jdk25u/master/src/java.base/share/classes/java/util/stream/Gatherers.java)
- So on JDK 21 a Java stream has no built-in counterpart to Kotlin's `chunked` / `windowed` / `runningFold` / `scan`. On JDK 24/25 it does, via `stream.gather(Gatherers.windowFixed(n))` and friends.

**JetBrains tooling guidance**
- The closest thing to official "when to use which" guidance is IntelliJ's K2 inspection `ConvertCallChainIntoSequenceInspection`:
  - message key `call.chain.on.collection.could.be.converted.into.sequence.to.improve.performance`;
  - `private val defaultCallChainLength = 5`, configurable 1–100;
  - chains at or above the threshold are highlighted (`GENERIC_ERROR_OR_WARNING`), shorter ones are only `INFORMATION`;
  - registered `enabledByDefault="true"`, `level="WEAK WARNING"`;
  - the quick-fix inserts `asSequence()`.

  — [IntelliJ inspection source](https://raw.githubusercontent.com/JetBrains/intellij-community/master/plugins/kotlin/code-insight/inspections-k2/src/org/jetbrains/kotlin/idea/codeInsight/inspections/collections/ConvertCallChainIntoSequenceInspection.kt); [inspection registration XML](https://raw.githubusercontent.com/JetBrains/intellij-community/master/plugins/kotlin/code-insight/inspections-k2/resources/intellij.kotlin.codeInsight.inspections.xml)
- Secondary (search snippets only, not fetched or verified): blog and forum posts say Kotlin built its own sequences rather than reuse Java 8 streams so they work on platforms without Java 8 APIs (mainly older Android), and that parallelism is the streams' main advantage. — [ProAndroidDev: Java Streams vs Kotlin Sequences](https://proandroiddev.com/java-streams-vs-kotlin-sequences-c9ae080abfdc) (unverified)

### Inferences

| Concern | Kotlin `Iterable` ops | Kotlin `Sequence` | Java `Stream` |
|---|---|---|---|
| Evaluation | eager; a new list per step | lazy, vertical | lazy, vertical |
| Reuse | always | usually; recomputes each time. Some are once-only (`IllegalStateException: This sequence can be consumed only once.`) | never (`IllegalStateException: stream has already been operated upon or closed`) |
| Parallel | no | no | `parallel()` / `parallelStream()` |
| Primitives | `IntArray`/`LongArray`; `List<Long>` is boxed | boxed only | `IntStream`/`LongStream`/`DoubleStream` |
| Terminal API | direct (`groupBy`, `associateBy`, `partition`, `sumOf` …) | same names | `collect(Collectors…)`, `toList()`, `reduce` → `Optional` |
| Duplicate map keys | last wins, silently | last wins, silently | `toMap` throws |
| Map ordering | `LinkedHashMap`, first-seen order | same | no guarantee (`HashMap` observed) |
| Windowing / scan | `chunked`, `windowed`, `runningFold`/`scan` | same, lazy | JDK 24+ `Gatherers` only |
| Lambda cost | inlined, no objects | one object per stage | one object per stage |
| Platforms | all Kotlin targets | all Kotlin targets | JVM only |

- **Practical guidance for a payments codebase:**
  - Use plain `Iterable` ops by default.
  - Use `asSequence()` for long chains over large inputs, or whenever the terminal operation short-circuits.
  - Use `sequence {}` / `generateSequence` for paging, retries and other lazily produced data.
  - Reach for Java streams only when you need `parallel()`, a `Gatherer`, primitive streams at scale, or a Java API that hands you a `Stream`.
- **A quick win when converting Java code:** replace `collect(groupingBy(f, counting()))` with `groupingBy(f).eachCount()`, and `mapToLong(f).sum()` with `sumOf(f)`.

### Gaps
- No official JetBrains statement was found comparing Sequences and Java Streams directly. The Java-to-Kotlin guide is silent, and the forum thread at discuss.kotlinlang.org was blocked.
- Kotlin in Action 2nd ed. could not be accessed. The often-quoted line that sequences are "the same concept" as Java 8 streams, created for Android/older-JVM compatibility, is unverified here.
- The Gatherers preview history (JDK 22/23 previews, final in 24) could not be verified because openjdk.org was blocked. Only `@since 24` in the source was confirmed.
- Parallel stream performance on Kotlin data was not measured.

---

## 4. What these operations compile to

### Takeaway
The two worlds compile very differently:
- `Iterable` operations (`map`, `filter`, `sumOf`, `groupBy`, `fold`, `forEach`, `first{}` …) are `inline`. The compiler copies the loop and the lambda body into the caller, so **no lambda objects are created and there are no `Function1.invoke` calls**. But you do get one `ArrayList` per step, and boxing whenever a primitive goes into a `List`.
- Sequence intermediate operations are ordinary functions. Each lambda becomes an `invokedynamic` + `LambdaMetafactory` `Function1` object, stored in a wrapper (`FilteringSequence`, `TransformingSequence`), and called through `invoke(Object): Object`, which boxes primitives.
- Kotlin 2.x generates no anonymous lambda classes by default.

### Cited Findings
- Why inline exists: "Using higher-order functions imposes certain runtime penalties: each function is an object, and it captures a closure … Memory allocations (both for function objects and classes) and virtual calls introduce runtime overhead." Also: "The `inline` modifier affects both the function itself and the lambdas passed to it: all of those will be inlined into the call site." — [Kotlin docs: Inline functions](https://kotlinlang.org/docs/inline-functions.html)
- Non-local return falls out of inlining: `ints.forEach { if (it == 0) return true // returns from hasZeros }`. — [Inline functions](https://kotlinlang.org/docs/inline-functions.html)
- `crossinline` marks lambdas that are called from another execution context. That is why `sortedBy(crossinline selector)` can build a `Comparator` while still being inline. — [Inline functions](https://kotlinlang.org/docs/inline-functions.html); [_Collections.kt](https://raw.githubusercontent.com/JetBrains/kotlin/v2.4.21/libraries/stdlib/common/src/generated/_Collections.kt)
- Kotlin 2.0 lambda compilation: "Kotlin 2.0.0 introduces a new default method for generating lambda functions using `invokedynamic`. This change reduces the binary sizes of applications compared to the traditional anonymous class generation."
  - Limitations: such lambdas are not serializable, the `reflect()` API does not support them, and `toString()` is less readable.
  - Opt-outs: `@JvmSerializableLambda`, or `-Xlambdas=class`.

  — [What's new in Kotlin 2.0.0](https://kotlinlang.org/docs/whatsnew20.html)
- Which functions are inline:
  - In `_Collections.kt`: `map`, `mapTo`, `filter`, `filterTo`, `mapNotNull`, `flatMap`, `fold`, `reduce`, `runningFold`, `scan`, `sumOf`, `groupBy`, `groupingBy` (crossinline keySelector), `associate*`, `partition`, `zip(other, transform)`, `distinctBy`, `sortedBy`, `takeWhile`, `maxByOrNull`, and the predicate overloads of `first`/`firstOrNull`/`any`/`all`/`none`/`count`.
  - Not inline: `first()`, `firstOrNull()`, `any()`, `none()` (without predicate), `Iterable.count()`, `chunked`, `windowed`, `zipWithNext()`.
  - In `_Sequences.kt`, `map`, `filter`, `mapNotNull`, `flatMap`, `take`, `sorted`, `distinctBy`, `chunked`, `windowed`, `zip`, `runningFold`, `scan` and `onEach` are `public fun`, not inline.

  — [_Collections.kt](https://raw.githubusercontent.com/JetBrains/kotlin/v2.4.21/libraries/stdlib/common/src/generated/_Collections.kt); [_Sequences.kt](https://raw.githubusercontent.com/JetBrains/kotlin/v2.4.21/libraries/stdlib/common/src/generated/_Sequences.kt)

**[local] `javap -c -p` of Kotlin 2.4.21 output** (`class P(val amountCents: Long, val status: St)`)

- **`fun eagerTotal(ps: List<P>) = ps.filter { it.status == St.SETTLED }.map { it.amountCents }.sum()`:**
  - `new java/util/ArrayList` + `ArrayList."<init>":()V`: filter's result, not pre-sized.
  - A fully inlined iterator loop: `Iterable.iterator`, `hasNext`, `next`, `checkcast P`, `P.getStatus`, `getstatic St.SETTLED`, `if_acmpne`, `Collection.add`.
  - `new java/util/ArrayList` + `CollectionsKt.collectionSizeOrDefault(Iterable, 10)` + `ArrayList."<init>":(I)V`: map's pre-sized result.
  - A second inlined loop: `P.getAmountCents:()J`, then **`java/lang/Long.valueOf`** (boxing), then `Collection.add`.
  - `invokestatic kotlin/collections/CollectionsKt.sumOfLong:(Ljava/lang/Iterable;)J`. `sum()` on `Iterable<Long>` is a regular call that unboxes.
  - **No `invokedynamic` and no `Function1` anywhere in the method.**
- **`fun sumOfTotal(ps) = ps.sumOf { if (it.status == St.SETTLED) it.amountCents else 0L }`:** one loop, `getAmountCents:()J`, `ladd`, `lreturn`. No allocation and no boxing; effectively the hand-written loop.
- **`fun lazyTotal(ps) = ps.asSequence().filter { … }.map { it.amountCents }.sum()`:**
  - `invokestatic CollectionsKt.asSequence`
  - `invokedynamic … invoke:()Lkotlin/jvm/functions/Function1;` → `invokestatic SequencesKt.filter(Sequence, Function1)`
  - a second `invokedynamic … Function1` → `SequencesKt.map`
  - `SequencesKt.sumOfLong(Sequence)J`

  The lambda bodies become `private static final boolean lazyTotal$lambda$0(P)` and `private static final long lazyTotal$lambda$1(P)`. The bootstrap arguments show `LambdaMetafactory.metafactory` with erased `(Ljava/lang/Object;)Ljava/lang/Object;` and instantiated `(LP;)Ljava/lang/Boolean;` / `(LP;)Ljava/lang/Long;`. So the predicate result and the mapped `long` are boxed at the `Function1` boundary.
- **Capturing lambda,** `fun capturing(ps, min: Long) = ps.asSequence().filter { it.amountCents >= min }.count()`: `invokedynamic … invoke:(J)Lkotlin/jvm/functions/Function1;`. The captured `min` is passed in, so a new `Function1` instance is produced each time the expression is evaluated. The body is `capturing$lambda$0(long, P)`.
- **Output directory:** only `P.class`, `St.class` and `BytecodeKt.class`. No `$1`/`$2` anonymous lambda classes, which confirms the 2.x `invokedynamic` default.
- **Kotlin lambda passed to a Java stream,** `ps.stream().filter { … }.mapToLong { … }.sum()`: in 2.4.21 each lambda compiled as an `invokedynamic` producing a Kotlin `Function1`, then a *second* `invokedynamic` wrapping it as `java.util.function.Predicate` / `ToLongFunction` (adapter methods `streamTotal$lambda$1(Function1, Object)Z` and `…$lambda$3(Function1, Object)J`).
  - The same happened with an explicit parameter `{ q: Q -> q.ok }`.
  - With the SAM-constructor form `filter(Predicate { it.ok })`, and for a non-generic Java SAM (`Runnable`), the compiler emitted a single `invokedynamic` directly to the Java interface.
  - This was observed only; I found no documentation explaining it. The cost is per pipeline construction plus one extra interface hop per element, which the JIT normally inlines.

Reproduce:

```
java -cp <kotlin-compiler-embeddable-2.4.21 + kotlin-stdlib + kotlin-script-runtime + kotlin-reflect + kotlin-daemon-embeddable + kotlinx-coroutines-core-jvm + jetbrains annotations> \
  org.jetbrains.kotlin.cli.jvm.K2JVMCompiler Bytecode.kt -d out -no-stdlib -classpath kotlin-stdlib-2.4.21.jar -jvm-target 21
javap -c -p -cp out BytecodeKt
javap -v -p -cp out BytecodeKt   # BootstrapMethods section shows LambdaMetafactory args
```

All of these jars are in `~/.gradle/caches/modules-2/files-2.1/`. The labs Gradle project uses Kotlin plugin 2.4.21, so `./gradlew :kotlin:compileKotlin` followed by `javap` on `build/classes` is the classroom route.

### Inferences
- **"Functional style allocates lambdas" is false for `Iterable` operations.** What actually costs is (a) the intermediate collection per step and (b) boxing when primitives are collected into `List<Long>`/`List<Int>`.
- **Sequences trade those costs for per-stage objects and megamorphic-prone `Function1.invoke` calls.** In hot code with many different lambdas passing through `FilteringSequence`, the JIT may fail to inline, and then the boxing comes back. That is why the docs hedge on overhead.
- **Because `forEach` is inline, `return` inside it returns from the enclosing function.** This surprises Java developers used to `Stream.forEach`, where `return` acts like `continue`. Use `return@forEach` to skip one element.

### Gaps
- I did not find a Kotlin document explaining the `Function1` → Java-SAM double `invokedynamic` seen for lambdas passed to generic Java SAM parameters such as `Stream.filter(Predicate<? super T>)`. Treat it as a 2.4.21 observation.
- The claim that HotSpot's `LambdaMetafactory` returns a shared instance for non-capturing lambdas is background knowledge. It was not verified in this session.

---

## 5. Common mistakes

### Takeaway
Most "functional Kotlin" performance and correctness bugs come from a handful of habits:
- materialising big intermediate lists;
- using `forEach` as a disguised loop that mutates outer state;
- rewriting nested loops (often O(n·m) joins) into dense chains;
- using `fold`/`reduce` where a purpose-built function (`sumOf`, `count`, `eachCount`, `maxByOrNull`, `mapNotNull`, `first {}`) says it better and handles the empty case;
- assuming a `List` is immutable, or that `associateBy` will catch duplicates.

### Cited Findings
- **Chaining many steps on huge lists.**
  - The docs: each eager step "completes and returns its result – an intermediate collection" — [Sequences](https://kotlinlang.org/docs/sequences.html).
  - **[local]** A 2-step `filter{}.map{}.sum()` on 1M payments allocated 26,507,194 B per call. A fused `sumOf{}` allocated about 0 B, and `asSequence()` about 189 B.
  - IntelliJ flags chains of ≥5 calls by default with a weak warning — [IntelliJ inspection](https://raw.githubusercontent.com/JetBrains/intellij-community/master/plugins/kotlin/code-insight/inspections-k2/src/org/jetbrains/kotlin/idea/codeInsight/inspections/collections/ConvertCallChainIntoSequenceInspection.kt).
- **forEach to mutate outer state.**
  - The Java docs call `forEach(s -> results.add(s))` an "Unnecessary use of side-effects!". In parallel, "the non-thread-safety of `ArrayList` would cause incorrect results". Side effects may also be elided: "With the exception of terminal operations `forEach` and `forEachOrdered`, side-effects of behavioral parameters may not always be executed when the stream implementation can optimize away the execution". — [package-info.java](https://raw.githubusercontent.com/openjdk/jdk21u/master/src/java.base/share/classes/java/util/stream/package-info.java)
  - **[local]** Sequential Kotlin `forEach { total += it }` gives the right answer (350), the same as `fold`/`sum`. The problem is clarity and composability, plus danger once the code moves to a parallel stream. A parallel run showed side-effect order ≠ encounter order.
- **Using fold or reduce where a purpose-built function exists.**
  - `sumOf` exists for exactly this.
  - `reduce` throws on empty with `UnsupportedOperationException("Empty collection can't be reduced.")`.
  - `reduce`'s accumulator must be a supertype of the element. The docs' own "incorrect" example uses `reduce { sum, e -> sum + e * 2 }`, which forgets to double the first element: 37 instead of 42.

  — [Aggregate operations](https://kotlinlang.org/docs/collection-aggregate.html); [_Collections.kt](https://raw.githubusercontent.com/JetBrains/kotlin/v2.4.21/libraries/stdlib/common/src/generated/_Collections.kt)
- **Paying for Pair objects.** `associate { a to b }` "produces short-living `Pair` objects which may affect the performance". `associateBy(key, value)` avoids the Pair. — [Collection transformations](https://kotlinlang.org/docs/collection-transformations.html)
- **Counting by groupBy.** `groupBy {}.mapValues { it.value.size }` builds a `List` per group. `groupingBy {}.eachCount()` builds none, and on the JVM it avoids boxing via `IntRef`. — [Grouping](https://kotlinlang.org/docs/collection-grouping.html); [GroupingJVM.kt](https://raw.githubusercontent.com/JetBrains/kotlin/v2.4.21/libraries/stdlib/jvm/src/kotlin/collections/GroupingJVM.kt)
- **Sorting in the middle of a sequence.** Sequence `sorted()` copies everything into a list when first iterated. **[local]** All 5 upstream elements were consumed before `first()` returned. — [_Sequences.kt](https://raw.githubusercontent.com/JetBrains/kotlin/v2.4.21/libraries/stdlib/common/src/generated/_Sequences.kt)
- **Re-iterating a sequence.** Doing so re-runs the pipeline and its side effects; once-only sequences throw `IllegalStateException`. — [Sequences.kt](https://raw.githubusercontent.com/JetBrains/kotlin/v2.4.21/libraries/stdlib/src/kotlin/collections/Sequences.kt); **[local]**
- **Assuming read-only means immutable.** The Kotlin docs say read-only collection types make mutation a compile error ("Unresolved reference: add") — [Collections in Java and Kotlin](https://kotlinlang.org/docs/java-to-kotlin-collections-guide.html). But **[local]** at runtime:
  - `map{}`'s result is a `java.util.ArrayList` and can be mutated after a cast;
  - `listOf(1,2)` is `java.util.Arrays$ArrayList`;
  - `buildList{}` gives a `ListBuilder` that rejects `add`.

### Inferences

**Rewrite patterns to teach.** Every row is a semantics-preserving replacement except the last.

| Instead of | Prefer | Why |
|---|---|---|
| `filter { p }.count()` | `count { p }` | one pass, no list |
| `filter { p }.first()` | `first { p }` | stops early, no list |
| `map { f }.filterNotNull()` | `mapNotNull { f }` | one list instead of two |
| `filter { p }.map { it.x }.sum()` | `sumOf { if (p) it.x else 0L }`, or `asSequence()` for a longer chain | no intermediate lists |
| `fold(0L) { a, p -> a + p.amount }` | `sumOf { it.amount }` | says what it means |
| `reduce { … }` on possibly-empty input | `fold(identity) { … }` or `reduceOrNull` | no exception on empty |
| `groupBy { k }.mapValues { it.value.size }` | `groupingBy { k }.eachCount()` | no per-group lists |
| `groupBy { k }.mapValues { it.value.sumOf { … } }` | `groupingBy { k }.fold(0L) { acc, e -> acc + e.amount }` | one pass |
| `associate { it.id to it }` | `associateBy { it.id }` | no Pair objects |
| `sortedBy { it.x }.first()` | `minByOrNull { it.x }` | O(n), not O(n log n); null-safe on empty (the `first()` version throws on empty) |

**Nested loops rewritten as chains.** Example: matching refunds to payments with

```kotlin
payments.flatMap { p -> refunds.filter { it.paymentId == p.id }.map { p to it } }
```

This is as O(n·m) as the nested loop it replaced, and it allocates an inner list per payment. Index once instead:

```kotlin
val byId = payments.associateBy { it.id }
refunds.mapNotNull { r -> byId[r.paymentId]?.let { it to r } }
```

That is O(n+m). When a chain needs more than one `Pair`/`Triple` juggling step, or nested `flatMap`s, a named intermediate `val` or a plain `for` loop with `buildList {}` is usually more readable. This advice is general style, inferred rather than sourced.

**forEach mutation patterns:**
- `forEach { if (ok) good += it else bad += it }` → `partition`.
- `forEach { totals[k] = (totals[k] ?: 0) + amt }` → `groupingBy { k }.fold(0L) { … }`.
- Mutating an outer `var` from a Java `parallelStream().forEach` is a data race. With Kotlin `forEach` it is "only" a style problem.

### Gaps
- No primary source quantifies how common these mistakes are. The list is drawn from the documented semantics plus the local measurements.

---

## Verified URLs

**Fetched and read in this session.** The raw GitHub files were downloaded with curl and grepped.
- https://kotlinlang.org/docs/sequences.html
- https://kotlinlang.org/docs/java-to-kotlin-collections-guide.html
- https://kotlinlang.org/docs/collection-aggregate.html (note: `collection-aggregate-operations.html` returns 404)
- https://kotlinlang.org/docs/collection-grouping.html
- https://kotlinlang.org/docs/collection-transformations.html
- https://kotlinlang.org/docs/collection-parts.html
- https://kotlinlang.org/docs/inline-functions.html
- https://kotlinlang.org/docs/whatsnew20.html
- https://raw.githubusercontent.com/JetBrains/kotlin/v2.4.21/libraries/stdlib/common/src/generated/_Collections.kt
- https://raw.githubusercontent.com/JetBrains/kotlin/v2.4.21/libraries/stdlib/common/src/generated/_Sequences.kt
- https://raw.githubusercontent.com/JetBrains/kotlin/v2.4.21/libraries/stdlib/src/kotlin/collections/Sequences.kt
- https://raw.githubusercontent.com/JetBrains/kotlin/v2.4.21/libraries/stdlib/src/kotlin/collections/SequenceBuilder.kt
- https://raw.githubusercontent.com/JetBrains/kotlin/v2.4.21/libraries/stdlib/src/kotlin/collections/Grouping.kt
- https://raw.githubusercontent.com/JetBrains/kotlin/v2.4.21/libraries/stdlib/jvm/src/kotlin/collections/GroupingJVM.kt
- https://raw.githubusercontent.com/JetBrains/kotlin/v2.4.21/libraries/stdlib/jdk8/src/kotlin/streams/Streams.kt (the path `libraries/stdlib/jvm/src/kotlin/streams/Streams.kt` returns 404)
- https://raw.githubusercontent.com/openjdk/jdk21u/master/src/java.base/share/classes/java/util/stream/package-info.java (source of the Oracle "package summary" text)
- https://raw.githubusercontent.com/openjdk/jdk21u/master/src/java.base/share/classes/java/util/stream/Stream.java
- https://raw.githubusercontent.com/openjdk/jdk21u/master/src/java.base/share/classes/java/util/stream/Collectors.java
- https://raw.githubusercontent.com/openjdk/jdk25u/master/src/java.base/share/classes/java/util/stream/Gatherers.java
- https://raw.githubusercontent.com/JetBrains/intellij-community/master/plugins/kotlin/code-insight/inspections-k2/src/org/jetbrains/kotlin/idea/codeInsight/inspections/collections/ConvertCallChainIntoSequenceInspection.kt
- https://raw.githubusercontent.com/JetBrains/intellij-community/master/plugins/kotlin/code-insight/inspections-k2/resources/intellij.kotlin.codeInsight.inspections.xml

**Canonical but not fetched (blocked host).** Content is equivalent to the OpenJDK sources above.
- https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/stream/package-summary.html

**Seen only as search results, not verified:**
- Effective Kotlin item "Prefer Sequence for big collections with more than one processing step": https://kt.academy/article/ek-sequence and https://www.codementor.io/@kotlin_academy/effective-kotlin-use-sequence-for-bigger-collections-with-more-than-one-processing-step-jqgbmnllp
- https://proandroiddev.com/java-streams-vs-kotlin-sequences-c9ae080abfdc

**Local verification environment:**
- Kotlin compiler 2.4.21 (`kotlin-compiler-embeddable`), kotlin-stdlib 2.4.21
- OpenJDK 21.0.12, JMH 1.37
- Probe sources in `/tmp/claude-0/-home-user/b1ec521c-18dd-5b5d-967f-de5283ba1787/scratchpad/kc/` and `/tmp/claude-0/-home-user/b1ec521c-18dd-5b5d-967f-de5283ba1787/scratchpad/bench/` (temporary)

---

## Teaching notes

### Misconceptions to address head-on
1. **"Kotlin collection ops are lazy, like streams."** No: `List.map/filter` are eager, and each step builds a full list. Only `Sequence` (and Java `Stream`) are lazy.
2. **"Lambdas in `map {}` allocate objects."** Not on `Iterable`: those functions are `inline`, and javap shows no `invokedynamic`. They do allocate on `Sequence` intermediate stages and on Java streams.
3. **"Always add `asSequence()`; it's faster."** The official docs say the overhead "may be significant" for small or simple cases. In the local run, a fused `sumOf` beat both the List chain and the Sequence. Laziness wins clearly when the terminal operation short-circuits, or when chains are long and inputs large.
4. **"`reduce` is `fold` without the boilerplate."** It differs on empty input (throws `UnsupportedOperationException`) and in typing (accumulator `S` must be a supertype of `T`).
5. **"Sequences are single-use like streams."** Most are reusable but recompute everything each time. Some (seedless `generateSequence`, `iterator().asSequence()`) throw on second use. Java streams are always single-use.
6. **"A sequence can be parallelised like a stream."** There is no parallel API on `Sequence`. For CPU parallelism, use `asStream().parallel()` (with a poorly splitting unknown-size spliterator), Java streams on the source collection, or coroutines.
7. **"`List<Long>` is a `long[]`."** It is boxed: `Long.valueOf` appears in the bytecode. Use `LongArray`, `sumOf`, or `LongStream`.
8. **"`listOf` / `map` results are immutable."** They are read-only *interfaces*. The runtime object is often a plain `ArrayList` that a cast can mutate.
9. **"`associateBy` will tell me about duplicates."** It keeps the last value silently. Java's `Collectors.toMap` throws `IllegalStateException`.
10. **"`return` inside `forEach` means continue."** In Kotlin it returns from the enclosing function because `forEach` is inline. Use `return@forEach`.

### Demo ideas, each with an expected outcome
1. **Horizontal vs vertical.** Run the `payments` `filter → map → take(2)` chain on a List and on a Sequence, with `println` in each lambda.
   - The List prints `filter 1..5` and then `map 1, 3, 5`.
   - The Sequence prints nothing until `toList()`, then `filter 1, map 1, filter 2, filter 3, map 3`. Payments 4 and 5 are never touched.
   - Both return `[1500, 2000]`.
2. **The `sorted` barrier.** `asSequence().onEach { println("saw ${it.id}") }.sortedBy { it.amountCents }.first()` prints `saw 1` … `saw 5`, then returns id 5. Ask the class to predict the output first.
3. **Java stream, same order, single use.** The same chain on `stream()` prints the same vertical order. Calling `count()` twice throws `IllegalStateException: stream has already been operated upon or closed`, while the `asSequence()` version can be iterated twice.
4. **Lazy paging with `sequence {}`.** Three pages with `println("fetching page $page")` and `.first { it > 15 }`. Expected: only pages 1 and 2 are fetched; the result is 20.
5. **Empty-input traps.** On `emptyList<Long>()`:
   - `fold(0L)` → 0, `sum()` → 0, `reduceOrNull` → null;
   - `reduce` → `UnsupportedOperationException: Empty collection can't be reduced.`;
   - `first()` → `NoSuchElementException: List is empty.`;
   - `maxOf {}` → `NoSuchElementException`;
   - Java `Stream.empty().reduce(...)` → `Optional.empty`.
6. **Duplicate keys.** `associateBy({ it.merchant }, { it.id })` → `{acme=3, globex=5, initech=4}`. Java `toMap` → `IllegalStateException: Duplicate key acme (attempted merging values 1 and 3)`.
7. **Bytecode reveal.** Compile `eagerTotal` / `lazyTotal` / `sumOfTotal` and run `javap -c -p`.
   - eager: two `new ArrayList`, `Long.valueOf`, no `invokedynamic`;
   - lazy: two `invokedynamic … Function1` + `SequencesKt.filter`/`map`;
   - `sumOf`: a single loop with `ladd`.
8. **Allocation with JMH `-prof gc`, at 1M payments:**
   - List chain about 26.5 MB per call;
   - boxed `stream().map().reduce()` about 28.8 MB per call;
   - Sequence about 0.2 KB;
   - `mapToLong().sum()` about 0.4 KB;
   - `sumOf` about 0.

   Short-circuit `firstOrNull` with a match at index 101: Sequence about 140 ns vs List about 4 ms. Re-run timings on a quiet machine; the allocation figures are stable.

### Exercise ideas
1. **Settlement report.** Given `List<Payment>`, return settled totals per merchant in cents in three ways: `groupBy + mapValues + sumOf`, `groupingBy().fold(0L)`, and a `for` loop. Check that all three are equal, and explain which builds per-group lists.
2. **Running balance.** Given a ledger of signed amounts, use `runningFold(0L)` (or `scan`) to produce balances. Then, lazily, find the index of the first overdraft. Bonus: do it over an infinite `generateSequence` of simulated transactions with `take`/`first`.
3. **Refund join.** Rewrite an O(n·m) `flatMap { refunds.filter { … } }` match into `associateBy` + `mapNotNull`. Write a test with duplicate `paymentId`s and decide what should happen (`groupBy` vs `associateBy`).
4. **Payout batching and trends.**
   - `chunked(100)` payouts into API batches;
   - `windowed(7)` moving average of daily volume;
   - `zipWithNext { a, b -> b - a }` day-over-day change.

   Predict the result sizes for n=10: `chunked(3)` → 4 chunks, `windowed(3)` → 8 windows, `zipWithNext` → 9.
5. **Fix the code.** A `forEach` that pushes into `good`/`bad` lists and a mutable `total` var. Rewrite with `partition` and `sumOf`. Then port it to Java `parallelStream().forEach` and explain why the original pattern breaks there.
6. **Java to Kotlin translation.** Convert:
   - `stream().filter(…).collect(groupingBy(Payment::getMerchant, counting()))` → `groupingBy { it.merchant }.eachCount()`
   - `mapToLong(Payment::getAmountCents).sum()` → `sumOf { it.amountCents }`
   - `collect(toMap(k, v, (a, b) -> b))` → `associateBy(k, v)`

   Note the ordering difference: `LinkedHashMap` vs no guarantee.
7. **Predict the output.** Give mixed List/Sequence chains with `println` side effects, including a `sorted()` in the middle and a sequence iterated twice. Students write the exact print order before running.
8. **Duplicate detector.** With `groupingBy { it.idempotencyKey }.eachCount().filterValues { it > 1 }`, flag duplicate submissions before an `associateBy` silently drops them.
