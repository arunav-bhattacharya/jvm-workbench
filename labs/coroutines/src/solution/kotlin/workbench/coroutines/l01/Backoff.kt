package workbench.coroutines.l01

import kotlinx.coroutines.delay

suspend fun pauseBeforeRetry(millis: Long) {
    // delay suspends the coroutine and gives the thread back; Thread.sleep would hold it
    delay(millis)
}
