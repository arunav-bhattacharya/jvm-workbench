package workbench.memory.l03

import java.util.WeakHashMap

data class KPhoto(val name: String)
data class KPreview(val width: Int)                                // knows nothing about its photo
data class KThumbnail(val source: KPhoto, val width: Int)          // refers back to its own key

/** WeakHashMap drops an entry when its key is unreachable, unless the value refers to the key. */
fun main() {
    val previews = WeakHashMap<KPhoto, KPreview>()
    val thumbnails = WeakHashMap<KPhoto, KThumbnail>()
    var beach: KPhoto? = KPhoto("beach.jpg")
    var dog: KPhoto? = KPhoto("dog.jpg")
    previews[beach!!] = KPreview(160)
    thumbnails[dog!!] = KThumbnail(dog, 160)

    beach = null                                                   // the photos are deleted: nothing else refers to them
    dog = null
    repeat(5) { System.gc(); Thread.sleep(20) }                    // demo only: ask for a few GCs

    println("previews left:   ${previews.size}")                   // size also removes cleared entries
    println("thumbnails left: ${thumbnails.size}")
}
