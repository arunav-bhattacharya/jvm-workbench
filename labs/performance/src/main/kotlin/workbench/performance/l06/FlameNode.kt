package workbench.performance.l06

/**
 * One box in a flame graph. [total] is the box's width: samples in this frame or in anything
 * called from it. Children are kept in alphabetical order, the way flamegraph.pl draws them.
 * This class is complete; you use it from FlameGraph.build.
 */
class FlameNode(val name: String) {
    var total: Long = 0

    private val kids = sortedMapOf<String, FlameNode>()

    /** Children in alphabetical order: the x-axis of a flame graph is not time. */
    val children: List<FlameNode> get() = kids.values.toList()

    /** Returns the child with this name, creating it the first time. */
    fun child(name: String): FlameNode = kids.getOrPut(name) { FlameNode(name) }

    /** Samples where this frame itself was on top: the exposed top edge of the box. */
    val self: Long get() = total - kids.values.sumOf { it.total }

    override fun toString() = "$name($total)"
}
