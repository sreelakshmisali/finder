import { type ReactNode } from "react";
import { motion } from "framer-motion";

interface PageWrapperProps {
  children: ReactNode;
}

const pageVariants = {
  initial: { opacity: 0, y: 12 },
  animate: { opacity: 1, y: 0 },
};

function PageWrapper({ children }: PageWrapperProps) {
  return (
    <motion.div
      variants={pageVariants}
      initial="initial"
      animate="animate"
      transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
      className="p-6 md:p-10 lg:p-12 w-full max-w-[1400px] mx-auto"
    >
      {children}
    </motion.div>
  );
}

export default PageWrapper;
