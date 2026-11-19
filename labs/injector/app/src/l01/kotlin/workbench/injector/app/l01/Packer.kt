package workbench.injector.app.l01

import workbench.injector.annotations.Inject

/** @Inject on the class means its primary constructor. */
@Inject
class Packer(val tape: TapeRoll)
