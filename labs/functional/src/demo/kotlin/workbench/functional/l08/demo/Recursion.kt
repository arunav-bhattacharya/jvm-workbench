package workbench.functional.l08.demo

/** Sums 1..n with recursion that is NOT in tail position: one stack frame per number. */
fun sumNaive(n: Long): Long = if (n == 0L) 0 else n + sumNaive(n - 1)

/** The same sum with an accumulator: the recursive call is the last thing it does. */
tailrec fun sumTo(n: Long, acc: Long = 0): Long = if (n == 0L) acc else sumTo(n - 1, acc + n)

/** A sourdough starter is fed from a spoonful of another starter. Walk back to the very first one. */
data class Starter(val id: String, val parentId: String?)

tailrec fun originOf(id: String, byId: Map<String, Starter>): String {
    val parent = byId.getValue(id).parentId ?: return id
    return originOf(parent, byId)
}

/** A recipe made of parts, each part made of parts: counting them is recursion that can't be put in tail form. */
class Part(val parts: List<Part>)

val countParts = DeepRecursiveFunction<Part, Long> { part ->
    var total = 1L
    for (child in part.parts) total += callRecursive(child)   // the "stack" lives on the heap
    total
}

fun main() {
    println("tailrec sumTo(1,000,000) = ${sumTo(1_000_000)}")
    try {
        println("sumNaive(1,000,000) = ${sumNaive(1_000_000)}")
    } catch (e: StackOverflowError) {
        println("sumNaive(1,000,000): StackOverflowError")
    }
    println("fold over 1..1,000,000 = ${(1L..1_000_000L).fold(0L) { acc, n -> acc + n }}")

    val family = (1..100_000).associate { i -> "s$i" to Starter("s$i", if (i == 1) null else "s${i - 1}") }
    println("origin of s100000 = ${originOf("s100000", family)}")

    var deep = Part(emptyList())
    repeat(100_000) { deep = Part(listOf(deep)) }   // absurdly deep, to make the point
    println("parts in a recipe nested 100,001 levels deep = ${countParts(deep)}")
}
