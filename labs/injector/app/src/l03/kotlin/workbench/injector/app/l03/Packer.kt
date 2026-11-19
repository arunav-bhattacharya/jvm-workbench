package workbench.injector.app.l03

import workbench.injector.annotations.Inject

/** A packer takes a fresh roll of tape for every room: `newTape()` builds one more each call. */
class Packer @Inject constructor(private val newTape: () -> TapeRoll) {
    fun pack(room: String): String = "$room packed with tape roll #${newTape().number}"
}
