package workbench.kotlin.l04.demo

@DslMarker
@Target(AnnotationTarget.CLASS, AnnotationTarget.TYPE)
annotation class FormDsl

data class Contact(val name: String, val phone: String)

data class OrderForm(val id: String, val copies: Int, val customer: Contact, val deliverTo: Contact)

@FormDsl
class ContactBuilder {
    var name = ""
    var phone = ""

    fun build(): Contact {
        require(phone.isNotBlank()) { "phone required for '$name'" }
        return Contact(name, phone)
    }
}

@FormDsl
class OrderFormBuilder(private val id: String) {
    var copies = 1
    private var customer: Contact? = null
    private var deliverTo: Contact? = null

    fun customer(block: ContactBuilder.() -> Unit) { customer = ContactBuilder().apply(block).build() }

    fun deliverTo(block: ContactBuilder.() -> Unit) { deliverTo = ContactBuilder().apply(block).build() }

    fun build() = OrderForm(id, copies, checkNotNull(customer) { "customer missing" }, checkNotNull(deliverTo) { "delivery address missing" })
}

fun orderForm(id: String, block: OrderFormBuilder.() -> Unit): OrderForm =
    OrderFormBuilder(id).apply(block).build()

fun main() {
    val form = orderForm("ord-17") {
        copies = 100
        customer { name = "Corner Bakery"; phone = "555-0142" }
        deliverTo {
            name = "Corner Bakery, back door"
            phone = "555-0143"
            this@orderForm.copies = 250              // an outer receiver needs an explicit label
        }
    }
    println(form)

    // Wrong move. Uncomment the block, predict, run. Then remove @FormDsl from both builder
    // classes and run it again.
    // orderForm("ord-18") {
    //     customer {
    //         name = "Corner Bakery"
    //         deliverTo { name = "oops" }
    //         phone = "555-0142"
    //     }
    // }
}
