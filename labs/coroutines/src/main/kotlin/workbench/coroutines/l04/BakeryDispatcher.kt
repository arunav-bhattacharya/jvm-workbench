package workbench.coroutines.l04

import kotlinx.coroutines.CoroutineDispatcher

/**
 * The bakery's old ordering client is blocking, and the bakery has 20 phone lines.
 *
 * Return a dispatcher, named "bakery", that runs at most 20 blocking bakery calls at the
 * same time, and does allow 20. Do not create a new thread pool.
 */
fun bakeryDispatcher(): CoroutineDispatcher {
    TODO("a view over Dispatchers.IO")
}
