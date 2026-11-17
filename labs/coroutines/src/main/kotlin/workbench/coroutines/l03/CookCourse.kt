package workbench.coroutines.l03

import kotlinx.coroutines.DelicateCoroutinesApi
import kotlinx.coroutines.GlobalScope
import kotlinx.coroutines.launch

/**
 * Cooks every dish of a course at the same time.
 *
 * Required behavior:
 * - returns only after every dish is done;
 * - if one dish fails, the others are cancelled and the failure is thrown to the caller;
 * - if the caller is cancelled, every dish is cancelled.
 *
 * This version leaks: it starts the work in GlobalScope and returns at once. Fix it.
 */
@OptIn(DelicateCoroutinesApi::class)
suspend fun cookCourse(dishes: List<String>, cook: suspend (String) -> Unit) {
    for (dish in dishes) {
        GlobalScope.launch { cook(dish) }
    }
}
