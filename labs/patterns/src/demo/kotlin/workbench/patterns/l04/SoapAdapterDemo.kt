package workbench.patterns.l04

import java.io.IOException

// A legacy SOAP client adapted to our port, plus a lambda adapter for a one-method port.

// the port our payment code depends on
fun interface PaymentGateway { fun charge(amountMinor: Long, currency: String, token: String): String }

// a vendor client we can't change: XML in, XML out, IOException on failure
class LegacySoapClient {
    @Throws(IOException::class)
    fun submitTxn(xml: String): String {
        if ("tok_down" in xml) throw IOException("SOAP fault: 503 Service Unavailable")
        val token = xml.substringAfter("tok='").substringBefore("'")
        return "<resp code='00' ref='R-${token.uppercase()}'/>"
    }
}

class GatewayUnavailable(message: String, cause: Throwable) : RuntimeException(message, cause)

// the adapter: implements our port, holds the vendor client, translates both ways
class SoapGatewayAdapter(private val soap: LegacySoapClient) : PaymentGateway {
    override fun charge(amountMinor: Long, currency: String, token: String): String {
        val xml = "<txn amt='$amountMinor' cur='$currency' tok='$token'/>"
        try {
            val resp = soap.submitTxn(xml)
            return resp.substringAfter("ref='").substringBefore("'")          // vendor format ends here
        } catch (e: IOException) {
            throw GatewayUnavailable("issuer unreachable", e)                 // our exception, not theirs
        }
    }
}

fun main() {
    val gateway: PaymentGateway = SoapGatewayAdapter(LegacySoapClient())
    println("charged, ref " + gateway.charge(1_250, "EUR", "tok_42"))
    try {
        gateway.charge(1_250, "EUR", "tok_down")
    } catch (e: Exception) {
        println("caller sees ${e.javaClass.simpleName}: ${e.message}")
    }
    // for a fun interface, a lambda is the adapter (SAM conversion)
    val quick = PaymentGateway { amount, _, _ -> "QUICK-$amount" }
    println("lambda adapter: " + quick.charge(990, "EUR", "tok_7"))
}
