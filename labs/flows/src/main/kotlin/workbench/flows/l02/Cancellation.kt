package workbench.flows.l02

import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.asFlow

/**
 * Predict, then check. A reconciliation job collects each flow below with a collector that cancels
 * its own coroutine when it sees 3, and never suspends. Which values does each collector get?
 *
 * Replace every TODO() with your prediction, for example `listOf(1, 2, 3)`. Commit to an answer
 * before you run the tests: CancellationTest compares your list with what really happens.
 */
object CancelPredictions {
    /** flow { for (i in 1..5) emit(i) } */
    val flowBuilderLoop: List<Int> get() = TODO("your prediction")

    /** (1..5).asFlow() */
    val asFlowRange: List<Int> get() = TODO("your prediction")

    /** flowOf(1, 2, 3, 4, 5) */
    val flowOfFive: List<Int> get() = TODO("your prediction")

    /** (1..5).asFlow().cancellable() */
    val asFlowCancellable: List<Int> get() = TODO("your prediction")

    /** (1..5).asFlow().map { it } */
    val asFlowMap: List<Int> get() = TODO("your prediction")

    /** (1..5).asFlow().transform { emit(it) } */
    val asFlowTransform: List<Int> get() = TODO("your prediction")
}

/**
 * The payment ids of a settlement batch, in order. The reconciliation job collects them and cancels
 * itself at the first mismatch. Its collector never suspends, and once it has cancelled, no more ids
 * may reach it.
 *
 * Bug: asFlow() does not check for cancellation between items.
 */
fun batchIds(ids: List<String>): Flow<String> = ids.asFlow()
