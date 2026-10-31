package workbench.jmm.l04

import kotlin.concurrent.thread

/** A constructor that starts a thread before it has finished setting its properties. */
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
    val sender = HeartbeatClient("issuer-gateway")
    println("constructor finished, endpoint = ${sender.endpoint}")
    Thread.sleep(100)
}

// stands in for a DNS or service-registry lookup
private fun resolve(name: String): String {
    Thread.sleep(50)
    return "https://$name.internal:8443"
}
