package workbench.patterns.l09

// Naive: an order with a status field, and four buttons that each check only what their author remembered.

enum class Status { PLACED, PACKED, OUT_FOR_DELIVERY, DELIVERED, CANCELLED }

class Order(val orderNo: String) {
    var status = Status.PLACED

    fun pack() {
        if (status == Status.PLACED) status = Status.PACKED
    }

    fun ship() {
        if (status == Status.PACKED) status = Status.OUT_FOR_DELIVERY
    }

    fun deliver() {
        status = Status.DELIVERED                               // no check: surely the driver knows
    }

    fun cancel() {
        if (status != Status.DELIVERED) status = Status.CANCELLED   // forgot: the van may have left
    }
}

fun main() {
    val o = Order("7781")
    o.pack()
    println("pack     -> ${o.status}")
    o.ship()
    println("ship     -> ${o.status}")
    o.cancel()                                                  // the customer presses Cancel; the van is on the road
    println("cancel   -> ${o.status}")
    o.deliver()                                                 // the driver hands the parcel over anyway
    println("deliver  -> ${o.status}")
    o.pack()                                                    // a stray click: nothing happens, and nobody says so
    println("pack     -> ${o.status}")
}
