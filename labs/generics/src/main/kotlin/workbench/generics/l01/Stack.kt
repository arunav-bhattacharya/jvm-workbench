package workbench.generics.l01

/**
 * A last-in, first-out stack of items of one type, T.
 *
 * Write the bodies. Keep the items in a private `MutableList<T>` that you add yourself.
 * You should not need a single cast: the type parameter does that work for you.
 */
class Stack<T> {
    /** How many items are on the stack. */
    val size: Int
        get() = TODO("return the number of items")

    /** True when the stack holds no items. */
    fun isEmpty(): Boolean = TODO("true when there are no items")

    /** Puts [item] on top of the stack. */
    fun push(item: T) {
        TODO("add the item on top")
    }

    /** Removes and returns the top item. Throws NoSuchElementException when the stack is empty. */
    fun pop(): T = TODO("remove and return the top item")

    /** Returns the top item without removing it, or null when the stack is empty. */
    fun peek(): T? = TODO("return the top item, or null")
}
