/**
 * UI Component Barrel Export
 *
 * This file re-exports all UI primitives from a single location.
 * Instead of importing from each file individually:
 *
 *   import Button from "../components/ui/Button";
 *   import Input from "../components/ui/Input";
 *
 * You can import everything from one place:
 *
 *   import { Button, Input, Card, Badge } from "../components/ui";
 */

export { default as Button } from "./Button";
export { default as Input } from "./Input";
export { Card, CardHeader, CardTitle } from "./Card";
export { default as Badge } from "./Badge";
export { default as Spinner } from "./Spinner";
export { default as Modal } from "./Modal";
export { default as Select } from "./Select";
