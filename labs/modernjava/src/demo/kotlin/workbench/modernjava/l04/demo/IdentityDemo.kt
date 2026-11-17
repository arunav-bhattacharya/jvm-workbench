package workbench.modernjava.l04.demo

// one physical copy of a book: its ISBN and its copy number
data class BookCopy(val isbn: String, val number: Int)

// Kotlin's value class today: one property, erased to that property wherever the compiler can
@JvmInline
value class Isbn(val value: String)

fun describeIsbn(isbn: Isbn): String = "ISBN ending ${isbn.value.takeLast(4)}"

/** Data classes are identity objects today; @JvmInline value classes are a compile-time trick. */
fun main() {
    val a = BookCopy("9780441013593", 1)
    val b = BookCopy("9780441013593", 1)

    println("==: ${a == b}, ===: ${a === b}")
    synchronized(a) {
        println("synchronized on a data class: allowed, because it has an identity")
    }

    val isbn = Isbn("9780441013593")
    println(describeIsbn(isbn))                                   // compiled to a call taking a plain String
    val asAny: Any = isbn                                         // used as another type: boxed
    println("as Any, the object is a ${asAny::class.java.simpleName}")
    val inList = listOf(isbn)                                     // used as a generic T: boxed
    println("in a List, the element is a ${(inList[0] as Any)::class.java.simpleName}")
}
