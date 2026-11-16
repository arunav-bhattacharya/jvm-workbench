package workbench.flows.l02

import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.asFlow
import kotlinx.coroutines.flow.cancellable

// Reference answer. Same names and signatures as src/main.

object CancelPredictions {
    val flowBuilderLoop: List<Int> get() = listOf(1, 2, 3)          // SafeCollector calls ensureActive on every emit
    val asFlowRange: List<Int> get() = listOf(1, 2, 3, 4, 5)        // asFlow is an unsafeFlow: no check between items
    val flowOfFive: List<Int> get() = listOf(1, 2, 3, 4, 5)         // flowOf too
    val asFlowCancellable: List<Int> get() = listOf(1, 2, 3)        // cancellable() adds ensureActive before each emit
    val asFlowMap: List<Int> get() = listOf(1, 2, 3, 4, 5)          // map is unsafe as well
    val asFlowTransform: List<Int> get() = listOf(1, 2, 3)          // the public transform is a SafeFlow
}

// cancellable() wraps the unsafe asFlow in a flow that calls ensureActive() before each emit
fun batchIds(ids: List<String>): Flow<String> = ids.asFlow().cancellable()
