package workbench.patterns.l09

// A customer's return as a state machine: states and events are data, the rules are one pure function.

sealed interface ReturnState {
    data class Requested(val id: String, val item: String) : ReturnState
    data class Approved(val id: String, val item: String, val approver: String) : ReturnState
    data class Collected(val id: String, val item: String, val label: String) : ReturnState
    data class BackOnShelf(val id: String, val item: String) : ReturnState
    data class Binned(val id: String, val reason: String) : ReturnState
}

sealed interface ReturnEvent {
    data class Approve(val approver: String) : ReturnEvent
    data class Collect(val label: String) : ReturnEvent
    data object PutBack : ReturnEvent
    data class Damaged(val reason: String) : ReturnEvent
}

private fun next(s: ReturnState, e: ReturnEvent): ReturnState = when (s) {   // no else: a new state breaks the build
    is ReturnState.Requested -> when (e) {
        is ReturnEvent.Approve if e.approver.isNotBlank() -> ReturnState.Approved(s.id, s.item, e.approver)
        else -> throw illegal(s, e)
    }
    is ReturnState.Approved -> when (e) {
        is ReturnEvent.Collect -> ReturnState.Collected(s.id, s.item, e.label)
        else -> throw illegal(s, e)
    }
    is ReturnState.Collected -> when (e) {
        ReturnEvent.PutBack -> ReturnState.BackOnShelf(s.id, s.item)
        is ReturnEvent.Damaged -> ReturnState.Binned(s.id, e.reason)
        else -> throw illegal(s, e)
    }
    is ReturnState.BackOnShelf, is ReturnState.Binned -> throw illegal(s, e)    // final
}

// a second when over the same states: the label on the shop's screen
private fun label(s: ReturnState): String = when (s) {
    is ReturnState.Requested -> "waiting for approval"
    is ReturnState.Approved -> "approved by ${s.approver}"
    is ReturnState.Collected -> "collected, label ${s.label}"
    is ReturnState.BackOnShelf -> "${s.item} is back on the shelf"
    is ReturnState.Binned -> "binned: ${s.reason}"
}

private fun illegal(s: ReturnState, e: ReturnEvent) =
    IllegalStateException("${e::class.simpleName} not allowed in ${s::class.simpleName}")

fun main() {
    var s: ReturnState = ReturnState.Requested("rt-31", "teapot")
    println(label(s))
    for (e in listOf(ReturnEvent.Approve("dana"), ReturnEvent.Collect("RT-0091"), ReturnEvent.PutBack)) {
        s = next(s, e)
        println(label(s))
    }
    try {
        next(ReturnState.Requested("rt-32", "kettle"), ReturnEvent.Collect("RT-0092"))
    } catch (ex: IllegalStateException) {
        println("rejected: ${ex.message}")
    }
}
