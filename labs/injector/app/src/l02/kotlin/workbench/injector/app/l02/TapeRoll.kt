package workbench.injector.app.l02

import workbench.injector.annotations.Inject

/** No @Singleton: every packer gets a new roll. */
class TapeRoll @Inject constructor() {
    val number: Int = ++made

    companion object {
        var made: Int = 0
            private set
    }
}
