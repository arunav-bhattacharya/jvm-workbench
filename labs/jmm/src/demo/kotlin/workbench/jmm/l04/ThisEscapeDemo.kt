package workbench.jmm.l04

import kotlin.concurrent.thread

/**
 * A constructor that starts a thread before it has finished setting its properties.
 * A heartbeat is a short "still running" message that one program sends another every few seconds.
 */
private class HeartbeatClient(endpointName: String) {
    val endpoint: String

    init {
        thread(name = "heartbeat") { sendHeartbeat() }   // `this` escapes to another thread here...
        endpoint = resolve(endpointName)                 // ...and this val is set about 50 ms later
    }

    fun sendHeartbeat() {
        println("heartbeat thread sends to: $endpoint")  // a non-null String that reads as null
    }
}

fun main() {
    val sender = HeartbeatClient("head-office")
    println("constructor finished, endpoint = ${sender.endpoint}")
    Thread.sleep(100)
}

// stands in for a slow lookup of the address over the network
private fun resolve(name: String): String {
    Thread.sleep(50)
    return "https://$name.example.com"
}
