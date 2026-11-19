package workbench.injector.app.l03

import workbench.injector.annotations.Inject

/** No @Singleton: a new roll every time one is asked for. */
class TapeRoll @Inject constructor() {
    val number: Int = ++made

    companion object {
        var made: Int = 0
            private set
    }
}
