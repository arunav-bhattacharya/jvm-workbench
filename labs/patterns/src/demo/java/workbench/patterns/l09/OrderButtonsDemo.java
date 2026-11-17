package workbench.patterns.l09;

/** Naive: an order with a status field, and four buttons that each check only what their author remembered. */
public class OrderButtonsDemo {
    enum Status { PLACED, PACKED, OUT_FOR_DELIVERY, DELIVERED, CANCELLED }

    static final class Order {
        final String orderNo;
        Status status = Status.PLACED;

        Order(String orderNo) { this.orderNo = orderNo; }

        void pack() {
            if (status == Status.PLACED) status = Status.PACKED;
        }

        void ship() {
            if (status == Status.PACKED) status = Status.OUT_FOR_DELIVERY;
        }

        void deliver() {
            status = Status.DELIVERED;                          // no check: surely the driver knows
        }

        void cancel() {
            if (status != Status.DELIVERED) status = Status.CANCELLED;   // forgot: the van may have left
        }
    }

    public static void main(String[] args) {
        Order o = new Order("7781");
        o.pack();
        System.out.println("pack     -> " + o.status);
        o.ship();
        System.out.println("ship     -> " + o.status);
        o.cancel();                                             // the customer presses Cancel; the van is on the road
        System.out.println("cancel   -> " + o.status);
        o.deliver();                                            // the driver hands the parcel over anyway
        System.out.println("deliver  -> " + o.status);
        o.pack();                                               // a stray click: nothing happens, and nobody says so
        System.out.println("pack     -> " + o.status);
    }
}
