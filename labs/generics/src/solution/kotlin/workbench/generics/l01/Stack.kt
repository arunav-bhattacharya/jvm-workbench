package workbench.generics.l01

class Stack<T> {
    // one private list of T: every push and pop is checked by the compiler, no casts anywhere
    private val items = mutableListOf<T>()

    val size: Int
        get() = items.size

    fun isEmpty(): Boolean = items.isEmpty()

    fun push(item: T) {
        items.add(item)
    }

    fun pop(): T {
        if (items.isEmpty()) throw NoSuchElementException("pop on an empty stack")
        return items.removeAt(items.lastIndex)   // the compiler knows this is a T
    }

    // T? means "a T, or null". If T is itself nullable (Stack<String?>), null is ambiguous here.
    fun peek(): T? = items.lastOrNull()
}
