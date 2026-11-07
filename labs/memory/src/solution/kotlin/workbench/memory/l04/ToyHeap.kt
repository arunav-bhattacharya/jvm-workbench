package workbench.memory.l04

class ToyHeap {
    private val refs = HashMap<Int, MutableSet<Int>>()
    private var nextId = 1

    fun allocate(): Int {
        val id = nextId++
        refs[id] = mutableSetOf()
        return id
    }

    fun link(from: Int, to: Int) {
        refs.getValue(from).add(to)
    }

    fun unlink(from: Int, to: Int) {
        refs.getValue(from).remove(to)
    }

    fun referencesOf(id: Int): Set<Int> = refs.getValue(id)

    fun contains(id: Int): Boolean = id in refs

    val size: Int get() = refs.size

    fun mark(roots: Collection<Int>): Set<Int> {
        val marked = HashSet<Int>()
        val toVisit = ArrayDeque(roots)              // the mark stack: objects found but not yet scanned
        while (toVisit.isNotEmpty()) {
            val id = toVisit.removeLast()
            if (!marked.add(id)) continue            // already marked: this is also what ends cycles
            for (next in refs.getValue(id)) {
                if (next !in marked) toVisit.addLast(next)
            }
        }
        return marked
    }

    fun sweep(marked: Set<Int>): Set<Int> {
        val dead = refs.keys.filterTo(HashSet()) { it !in marked }   // visits every object, live or dead
        refs.keys.removeAll(dead)                                     // their memory is free again
        return dead
    }

    fun collect(roots: Collection<Int>): Set<Int> = sweep(mark(roots))
}
