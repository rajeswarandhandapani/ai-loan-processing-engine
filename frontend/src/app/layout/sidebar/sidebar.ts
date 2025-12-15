import { Component, signal } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';

interface NavItem {
  icon: string;
  label: string;
  route: string;
}

@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [RouterLink, RouterLinkActive],
  templateUrl: './sidebar.html',
  styleUrl: './sidebar.scss'
})
export class SidebarComponent {
  isCollapsed = signal(false);
  
  navItems: NavItem[] = [
    { icon: 'bi-house-door', label: 'Home', route: '/' },
    { icon: 'bi-file-earmark-text', label: 'Loan Application', route: '/loan-application' },
    { icon: 'bi-upload', label: 'Upload Documents', route: '/upload' },
    { icon: 'bi-chat-dots', label: 'AI Assistant', route: '/chat' },
    { icon: 'bi-graph-up', label: 'Dashboard', route: '/dashboard' }
  ];

  toggleSidebar() {
    this.isCollapsed.update(v => !v);
  }
}
