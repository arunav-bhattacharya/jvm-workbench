package workbench.patterns.l04

import java.math.BigDecimal
import java.util.Currency

// A vendor DTO from the issuer SDK, with its names and units.
class VendorTxn(val txnRef: String, val amt: String, val ccyNum: String, val respCd: String)

// Our domain type.
data class Receipt(val reference: String, val amountMinor: Long, val currency: String, val approved: Boolean)

// An extension function is a lightweight adapter: it reads like a method on the vendor type,
// lives in our code, and keeps the mapping in one place.
fun VendorTxn.toReceipt(): Receipt {
    val currency = Currency.getAvailableCurrencies().first { it.numericCode == ccyNum.toInt() }
    return Receipt(
        reference = txnRef,
        amountMinor = BigDecimal(amt).movePointRight(currency.defaultFractionDigits).longValueExact(),
        currency = currency.currencyCode,
        approved = respCd == "00",
    )
}

fun main() {
    val fromSdk = listOf(
        VendorTxn("T-1001", "12.50", "978", "00"),
        VendorTxn("T-1002", "1250", "392", "00"),
        VendorTxn("T-1003", "99.99", "840", "51"),
    )
    fromSdk.map { it.toReceipt() }.forEach(::println)
}
