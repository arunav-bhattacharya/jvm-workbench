package workbench.generics.l07

/**
 * One line for a debug log, whatever [value] is. Check the cases in this order:
 *
 * - `null`                -> "nothing"
 * - a String              -> "text " + the string, such as "text EUR"
 * - a List of anything    -> "list of " + its size, such as "list of 3"
 * - a Map of anything     -> "map of " + its size
 * - a Number              -> "number " + its toString(), such as "number 1200"
 * - anything else         -> "other"
 *
 * You can't write `value is List<String>`: type arguments are erased. Use a star projection.
 */
fun describe(value: Any?): String =
    TODO("use `when (value)` with `is List<*>` and `is Map<*, *>` branches")

/**
 * If [value] is a list, return its String elements in their original order. Otherwise return an
 * empty list. After `value is List<*>`, every element is only known to be Any?, so check each one.
 */
fun stringsIn(value: Any?): List<String> =
    TODO("smart-cast to List<*>, then keep the elements that are Strings")

/**
 * Removes every element from [buffer] and returns how many were removed.
 *
 * TODO: this function never reads or adds an element, so it should accept a mutable list of ANY
 * element type: a MutableList<String>, a MutableList<Int>... Today it only accepts MutableList<Any?>,
 * which is invariant: `drain(mutableListOf("pay_1"))` does not compile. Fix the parameter type
 * (Java will then see `List<?>`), then write the body.
 */
fun drain(buffer: MutableList<Any?>): Int =
    TODO("fix the parameter type, then clear the buffer")
