package workbench.memory.l04

/**
 * A toy heap for a toy mark-and-sweep collector. Objects are just numbers, and each object can hold
 * references to others, like reference fields. Write [mark] and [sweep]; [collect] runs both.
 */
class ToyHeap {
    private val refs = HashMap<Int, MutableSet<Int>>()   // object id -> the ids its fields point to
    private var nextId = 1

    /** Creates an object with no references and returns its id. */
    fun allocate(): Int {
        val id = nextId++
        refs[id] = mutableSetOf()
        return id
    }

    /** Stores a reference to [to] in one of [from]'s fields. */
    fun link(from: Int, to: Int) {
        refs.getValue(from).add(to)
    }

    /** Clears that reference again. */
    fun unlink(from: Int, to: Int) {
        refs.getValue(from).remove(to)
    }

    /** The ids [id] points to. */
    fun referencesOf(id: Int): Set<Int> = refs.getValue(id)

    fun contains(id: Int): Boolean = id in refs

    val size: Int get() = refs.size

    /**
     * Mark: every object reachable from [roots] by following references, roots included.
     * Must terminate on cycles, and must not recurse: a chain of 200,000 objects would overflow
     * the thread's stack. Keep your own stack of objects still to visit, as a real collector does.
     */
    fun mark(roots: Collection<Int>): Set<Int> {
        TODO("walk the graph from the roots with an explicit stack")
    }

    /** Sweep: removes every object that is not in [marked] and returns the removed ids. */
    fun sweep(marked: Set<Int>): Set<Int> {
        TODO("remove every unmarked object")
    }

    /** One full collection: mark from the roots, then sweep. Returns what was freed. */
    fun collect(roots: Collection<Int>): Set<Int> = sweep(mark(roots))
}
