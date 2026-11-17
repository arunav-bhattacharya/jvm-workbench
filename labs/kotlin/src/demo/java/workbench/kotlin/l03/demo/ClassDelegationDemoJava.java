package workbench.kotlin.l03.demo;

/**
 * Java twin of ClassDelegationDemo.kt. Java has no `by`, so you write the forwarding yourself.
 * Written by hand, it reads the field on every call, so swapping the printer works.
 */
public class ClassDelegationDemoJava {

    static final class FrontDeskJava implements Printer {
        private Printer printer;

        FrontDeskJava(Printer printer) { this.printer = printer; }

        void setPrinter(Printer printer) { this.printer = printer; }

        @Override
        public String print(String document) {
            return printer.print(document);              // reads the current field each time
        }
    }

    public static void main(String[] args) {
        FrontDeskJava desk = new FrontDeskJava(new Laser("laser-1"));
        System.out.println(desk.print("flyer.pdf"));
        desk.setPrinter(new Laser("laser-2"));
        System.out.println("after swap: " + desk.print("flyer.pdf"));

        // the Kotlin class, seen from Java: setPrinter changes the property, not the $$delegate_0 field
        FrontDesk kotlinDesk = new FrontDesk(new Laser("laser-1"));
        kotlinDesk.setPrinter(new Laser("laser-2"));
        System.out.println("Kotlin class after swap: " + kotlinDesk.print("flyer.pdf"));
    }
}
