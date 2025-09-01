export type ColorVariant = 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'neutral';
export type SizeVariant = 'xs' | 'sm' | 'md' | 'lg' | 'xl';
export type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'outline';

export interface ComponentProps {
  className?: string;
  children?: React.ReactNode;
}

export interface ButtonProps extends ComponentProps {
  variant?: ButtonVariant;
  size?: SizeVariant;
  disabled?: boolean;
  loading?: boolean;
  onClick?: () => void;
  type?: 'button' | 'submit' | 'reset';
}

export interface CardProps extends ComponentProps {
  hover?: boolean;
  padding?: SizeVariant;
}

export interface BadgeProps extends ComponentProps {
  variant?: ColorVariant;
  size?: SizeVariant;
  icon?: React.ComponentType<{ className?: string }>;
}
