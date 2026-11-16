package workbench.flows.l04

import kotlinx.coroutines.channels.Channel
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.launch

fun <T> Flow<T>.belt(capacity: Int): Flow<T> = flow {
    coroutineScope {
        val slots = Channel<T>(capacity)        // the belt: `capacity` slots between two coroutines
        launch {                                 // 1. a second coroutine runs the upstream
            try {
                collect { slots.send(it) }       //    send suspends only when every slot is full
            } finally {
                slots.close()                    //    no more values: lets the loop below end
            }
        }
        for (value in slots) emit(value)         // 2. our own coroutine takes one and hands it on;
    }                                            //    an upstream failure fails the launch, and so this scope
}
