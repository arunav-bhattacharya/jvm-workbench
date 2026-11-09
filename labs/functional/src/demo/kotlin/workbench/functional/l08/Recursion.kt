package workbench.functional.l08

/** Sums 1..n with recursion that is NOT in tail position: one stack frame per number. */
fun sumNaive(n: Long): Long = if (n == 0L) 0 else n + sumNaive(n - 1)

/** The same sum with an accumulator: the recursive call is the last thing it does. */
tailrec fun sumTo(n: Long, acc: Long = 0): Long = if (n == 0L) acc else sumTo(n - 1, acc + n)

/** A refund of a refund of a refund: walk back to the original payment. */
data class Txn(val id: String, val parentId: String?)

tailrec fun originOf(id: String, byId: Map<String, Txn>): String {
    val parent = byId.getValue(id).parentId ?: return id
    return originOf(parent, byId)
}

/** A merchant hierarchy: counting the nodes is recursion that can't be put in tail form. */
class Node(val children: List<Node>)

val countNodes = DeepRecursiveFunction<Node, Long> { node ->
    var total = 1L
    for (child in node.children) total += callRecursive(child)   // the "stack" lives on the heap
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

    val chain = (1..100_000).associate { i -> "t$i" to Txn("t$i", if (i == 1) null else "t${i - 1}") }
    println("origin of t100000 = ${originOf("t100000", chain)}")

    var deep = Node(emptyList())
    repeat(100_000) { deep = Node(listOf(deep)) }
    println("nodes in a tree 100,001 levels deep = ${countNodes(deep)}")
}
